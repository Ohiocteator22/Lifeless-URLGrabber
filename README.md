<div align="center">

# URLGrab

**Paste. Pick. Download.**

A sleek, modern desktop video downloader built with Python.

![Python](https://img.shields.io/badge/Python-3.10%2B-7c5cff?style=flat-square&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-10b981?style=flat-square&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-7c5cff?style=flat-square)
![Powered by yt-dlp](https://img.shields.io/badge/Powered%20by-yt--dlp-10b981?style=flat-square)

</div>

---

## ✨ What is URLGrab?

URLGrab is a lightweight desktop app that downloads videos from **1800+ websites** in any resolution they offer — from 4K down to SD. Paste a link, pick your quality, hit download. No ads, no bloat, no browser extension.

<div align="center">
┌──────────────────────────────────────────┐
│ URLGrab │
│ Paste a link. Pick a quality. Done. │
│ │
│ VIDEO URL │
│ ┌──────────────────────────┐ ┌──────┐ │
│ │ youtube.com/watch?v=... │ │Fetch │ │
│ └──────────────────────────┘ └──────┘ │
│ │
│ AVAILABLE FORMATS │
│ ┌────────────────────────────────────┐ │
│ │ 4K 2160p .mp4 1.2 GB │ │
│ │ 2K 1440p .mp4 640 MB │ │
│ │ FHD 1080p .mp4 220 MB │ │
│ │ HD 720p .mp4 110 MB │ │
│ └────────────────────────────────────┘ │
│ │
│ 📁 Choose Folder ⬇ Download │
└──────────────────────────────────────────┘

text

</div>

## 🚀 Features

- 🎬 **Multi-resolution** — 4K, 2K, FHD, HD, SD, and more
- 📦 **MP4 & MKV** — pick your container
- ⚡ **Fast** — parallel fragment downloads + optional aria2c acceleration
- 🍪 **Cookie support** — download from Instagram, Facebook, and other sites that need login
- 🎨 **Modern dark UI** — clean, minimal, no clutter
- 📊 **Live progress** — real-time speed and percentage
- 🖥️ **One-file exe** — no Python install required for end users

## 🌐 Supported Sites

URLGrab is powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp), which supports **1800+ sites** out of the box, including:

| Site | Support |
|------|---------|
| YouTube | ✅ |
| TikTok | ✅ |
| Twitter / X | ✅ |
| Reddit | ✅ |
| Vimeo | ✅ |
| Twitch (VODs) | ✅ |
| Dailymotion | ✅ |
| Instagram | ⚠️ requires `cookies.txt` |
| Facebook | ⚠️ requires `cookies.txt` |

## 📥 Installation

### Option 1 — Download the prebuilt exe

Grab the latest `URLGrab.exe` from the [Releases](../../releases) page. Double-click and you're done. No install, no dependencies.

### Option 2 — Run from source

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/URLGrab.git
cd URLGrab

# Install Python dependencies
pip install yt-dlp ttkbootstrap

# Get FFmpeg (required for merging HD video + audio)
# Download from https://github.com/yt-dlp/FFmpeg-Builds/wiki/Latest
# Extract and place ffmpeg.exe + ffprobe.exe next to URLGrab.py

# Optional: aria2c for max speed
# Download from https://github.com/aria2/aria2/releases
# Extract aria2c.exe next to URLGrab.py

# Run it
python URLGrab.py
