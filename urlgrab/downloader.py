import os

import yt_dlp

from .config import FFMPEG_DIR, ARIA2C_PATH


def fetch_formats(url, cookie_opts=None):
    """Return the raw yt-dlp info dict for `url`, or raise on error."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        **(cookie_opts or {}),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def filter_and_sort_formats(formats):
    """Dedupe by (height, container), keep the best bitrate per bucket,
    return sorted highest-first."""
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


def build_ydl_opts(format_selector, out_dir, merge_ext, cookie_opts, progress_hook):
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