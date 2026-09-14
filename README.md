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

| Site          | Support                   |
| ------------- | ------------------------- |
| YouTube       | ✅                        |
| TikTok        | ✅                        |
| Twitter / X   | ✅                        |
| Reddit        | ✅                        |
| Vimeo         | ✅                        |
| Twitch (VODs) | ✅                        |
| Dailymotion   | ✅                        |
| Instagram     | ⚠️ requires `cookies.txt` |
| Facebook      | ⚠️ requires `cookies.txt` |

## 📥 Installation

### Option 1 — Download the prebuilt exe

Grab the latest `URLGrab.exe` from the [Releases](../../releases) page. Double-click and you're done. No install, no dependencies.

### Option 2 — Run from source

````bash
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


# 🍎 macOS Support

URLGrab **supports macOS**, but there isn't currently a pre-built `.app`
bundled with the release.

But guess what?

**YOU can build it yourself.**

### 🛠️ How to build

1. Download the URLGrab repository as a `.zip`.
2. Extract the ZIP somewhere.
3. Open **Terminal** inside the extracted repository.
4. Run:

   ```bash
   bash build-macos.sh
````

Wait for the build to finish. (First run takes 2–5 minutes.)

You'll get a working macOS build at dist/URLGrab.app.

Once you've built it, you can delete the repository folder and the
original ZIP if you don't need them anymore.

🍺 Prerequisites
Python 3.10+ — pre-installed on most Macs, or via python.org

Homebrew (optional) — only needed for the aria2c download accelerator

Xcode Command Line Tools — if iconutil is missing, run xcode-select --install

🚪 First launch warning
macOS will warn that URLGrab is from an "unidentified developer." This is
normal — the app isn't code-signed.

To open it anyway:

Right-click the app → Open → Open

Or run once: xattr -cr dist/URLGrab.app

⚠️ Known limitation
If you want the latest version of URLGrab, you'll need to repeat this
process whenever a new version is released.

Why is this happening?
Steve Jobs.

(More specifically: Apple charges $99/year for code signing certificates,
and shipping an unsigned binary in a GitHub release is a support nightmare
because every user hits the Gatekeeper warning. Building locally sidesteps
the whole problem.)

text

---

### 🎯 Why this is the right approach

- **One command** — `bash build-macos.sh` does everything
- **Self-healing** — each step checks if the file already exists
- **No hidden assumptions** — works on Intel and Apple Silicon
- **No expensive deps** — Homebrew is optional, everything else is free
- **Steve Jobs joke stays** — that line is gold

Commit both, tag `v1.1.9`, push. The GitHub Actions build will _also_ work if you ever set that up — but for now, this README solution is honest and simple.
