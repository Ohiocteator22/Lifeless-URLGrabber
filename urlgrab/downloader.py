import os

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


def build_format_selector(height):
    return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"


def parse_timecode(text):
    """Parse 'HH:MM:SS', 'MM:SS', or 'SS' into seconds.
    Returns None if the string is empty or unparseable."""
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
):
    ydl_opts = {
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
        ydl_opts.update(
            {
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": [
                    s.strip() for s in str(subtitle_langs).split(",") if s.strip()
                ] or ["en"],
                "subtitlesformat": "srt/best",
            }
        )

    if thumbnail:
        ydl_opts["writethumbnail"] = True

    if trim_start is not None or trim_end is not None:
        start = trim_start if trim_start is not None else 0
        end = trim_end

        def _ranges(info_dict, ydl):
            return [{"start_time": start, "end_time": end}]

        ydl_opts["download_ranges"] = _ranges
        ydl_opts["force_keyframes_at_cuts"] = True

    if ARIA2C_PATH:
        ydl_opts.update(
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

    return ydl_opts


def build_audio_ydl_opts(
    out_dir,
    bitrate,
    cookie_opts,
    progress_hook,
    audio_format="mp3",
):
    ydl_opts = {
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
        ydl_opts.update(
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

    return ydl_opts


def download(url, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])