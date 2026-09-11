import os
import shlex

import yt_dlp

from .config import FFMPEG_DIR, ARIA2C_PATH


def fetch_formats(url, cookie_opts=None):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        **(cookie_opts or {}),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def filter_and_sort_formats(formats):
    best_by_key = {}
    for f in formats:
        if f.get("vcodec") in (None, "none"):
            continue
        height = f.get("height")
        if not height:
            continue
        ext = f.get("ext", "mp4")
        key = (height, ext)
        prev = best_by_key.get(key)
        if prev is None or (f.get("tbr") or 0) > (prev.get("tbr") or 0):
            best_by_key[key] = f

    return sorted(
        best_by_key.values(),
        key=lambda x: (x["height"], x.get("tbr") or 0),
        reverse=True,
    )


# ----------------------------------------------------------------------
# Codec / HDR label shortening
# ----------------------------------------------------------------------
def shorten_vcodec(codec):
    if not codec or codec == "none":
        return "—"
    c = codec.lower()
    if c.startswith("avc") or c.startswith("h264"):
        return "h264"
    if c.startswith("hvc") or c.startswith("hev") or c.startswith("h265"):
        return "h265"
    if c.startswith("av01") or c.startswith("av1"):
        return "av1"
    if c.startswith("vp09") or c.startswith("vp9"):
        return "vp9"
    if c.startswith("vp8"):
        return "vp8"
    return c.split(".")[0][:8]


def shorten_acodec(codec):
    if not codec or codec == "none":
        return "—"
    c = codec.lower()
    if c.startswith("mp4a") or c.startswith("aac"):
        return "aac"
    if c.startswith("opus"):
        return "opus"
    if c.startswith("vorbis"):
        return "vorbis"
    if c.startswith("mp3"):
        return "mp3"
    if c.startswith("ac-3") or c.startswith("eac3") or c.startswith("ac3"):
        return "ac3"
    return c.split(".")[0][:8]


def hdr_label(fmt):
    dr = fmt.get("dynamic_range") or ""
    if not dr or dr.upper() == "SDR":
        return "—"
    return dr


# ----------------------------------------------------------------------
# Custom args parsing
# ----------------------------------------------------------------------
def parse_custom_args(raw):
    """Turn a raw yt-dlp CLI string into an opts dict.
    Returns (opts_dict, error_message_or_None)."""
    if not raw or not raw.strip():
        return {}, None

    try:
        from yt_dlp import parse_options
    except ImportError:
        try:
            from yt_dlp.options import parseOpts as parse_options
        except ImportError:
            return {}, "yt-dlp parse_options is unavailable"

    try:
        tokens = shlex.split(raw, posix=True)
        _, opts, _ = parse_options(tokens)
        return opts or {}, None
    except Exception as e:
        return {}, str(e)


# ----------------------------------------------------------------------
# Selector / timecode helpers
# ----------------------------------------------------------------------
def build_format_selector(height):
    return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"


def parse_timecode(text):
    if text is None:
        return None
    text = str(text).strip()
    if not text:
        return None
    parts = text.split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        return None
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 1:
        return parts[0]
    return None


# ----------------------------------------------------------------------
# Build opts
# ----------------------------------------------------------------------
def build_ydl_opts(
    format_selector,
    out_dir,
    merge_ext,
    cookie_opts,
    progress_hook,
    subtitles=False,
    subtitle_langs="en",
    thumbnail=False,
    trim_start=None,
    trim_end=None,
    sponsorblock=False,
    sponsorblock_categories="sponsor,selfpromo",
    custom_args="",
):
    custom_opts, _ = parse_custom_args(custom_args)

    our_opts = {
        "format": format_selector,
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "merge_output_format": merge_ext,
        "ffmpeg_location": FFMPEG_DIR,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "progress_hooks": [progress_hook],
        "concurrent_fragment_downloads": 10,
        "http_chunk_size": 10485760,
        "retries": 10,
        "fragment_retries": 10,
        "buffersize": 1024 * 1024,
        **(cookie_opts or {}),
    }

    if subtitles:
        langs = [
            s.strip() for s in str(subtitle_langs).split(",") if s.strip()
        ] or ["en"]
        our_opts.update(
            {
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": langs,
                "subtitlesformat": "srt/best",
            }
        )

    if thumbnail:
        our_opts["writethumbnail"] = True

    if trim_start is not None or trim_end is not None:
        start = trim_start if trim_start is not None else 0
        end = trim_end

        def _ranges(info_dict, ydl):
            return [{"start_time": start, "end_time": end}]

        our_opts["download_ranges"] = _ranges
        our_opts["force_keyframes_at_cuts"] = True

    if sponsorblock:
        cats = [
            c.strip() for c in str(sponsorblock_categories).split(",") if c.strip()
        ]
        our_opts["sponsorblock_remove"] = set(cats or ["sponsor"])

    if ARIA2C_PATH:
        our_opts.update(
            {
                "external_downloader": ARIA2C_PATH,
                "external_downloader_args": {
                    "aria2c": [
                        "-x", "16",
                        "-s", "16",
                        "-k", "1M",
                        "--min-split-size=1M",
                        "--max-connection-per-server=16",
                        "--file-allocation=none",
                        "--console-log-level=warn",
                        "--summary-interval=0",
                    ]
                },
            }
        )

    # Custom args go first, our keys win on collisions
    return {**custom_opts, **our_opts}


def build_audio_ydl_opts(
    out_dir,
    bitrate,
    cookie_opts,
    progress_hook,
    audio_format="mp3",
    custom_args="",
):
    custom_opts, _ = parse_custom_args(custom_args)

    our_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "ffmpeg_location": FFMPEG_DIR,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "progress_hooks": [progress_hook],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": str(bitrate),
            }
        ],
        "concurrent_fragment_downloads": 10,
        "retries": 10,
        "fragment_retries": 10,
        **(cookie_opts or {}),
    }

    if ARIA2C_PATH:
        our_opts.update(
            {
                "external_downloader": ARIA2C_PATH,
                "external_downloader_args": {
                    "aria2c": [
                        "-x", "16",
                        "-s", "16",
                        "-k", "1M",
                        "--min-split-size=1M",
                        "--max-connection-per-server=16",
                        "--file-allocation=none",
                        "--console-log-level=warn",
                        "--summary-interval=0",
                    ]
                },
            }
        )

    return {**custom_opts, **our_opts}


def download(url, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])