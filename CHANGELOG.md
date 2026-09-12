# Changelog

All notable changes to URLGrab are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

Releases tagged `FD` are **Feature-Dense** — they pack multiple
substantial features together rather than a single-focused bump.

---

## [Unreleased]

_Nothing yet — ideas live in the issue tracker._

---

## [1.1.7FD] - 2024-XX-XX

**Feature-Dense release.** Turns URLGrab into a proper desktop app
with tray integration, drag-and-drop, and a built-in log viewer.

### Added
- **System tray icon** — minimize instead of quitting
  - Right-click menu: Show URLGrab / New download / Quit
  - Toggle in SETTINGS → System (on by default)
  - Falls back gracefully if `pystray` isn't installed
- **Drag-and-drop URLs** — drop a link from any browser onto the window
  - Accepts text drops and file-list drops
  - Extracts the first valid URL from multi-item drops
  - Falls back silently if `tkinterdnd2` isn't installed
- **LOG tab** — full activity viewer for sharing errors
  - Captures logger output, stderr, and uncaught exceptions
  - Color-coded by severity: INFO / DEBUG / WARNING / ERROR
  - Buttons: Copy All, Save to File, Clear
  - Capped at 500 lines in memory
- New modules: `logger.py`, `tray.py`, `ui/log_tab.py`
- New dependencies: `pystray`, `Pillow`, `tkinterdnd2`

### Changed
- **Window icon fix** — `icon.ico` now resolves correctly in both dev
  mode (project root) and frozen mode (`_MEIPASS`)
- **Close button** now minimizes to tray when the tray is active and
  `tray_on_close` is enabled. Real quit only via tray menu
- `app.py` installs the logger and exception hook on startup
- SETTINGS gains a new **System** section for the tray toggle

---

## [1.1.6FD] - 2024-XX-XX

**Feature-Dense release.** Ships the entire power-user toolkit in one
drop — settings, themes, onboarding, updates, and notifications.

### Added
- **SETTINGS tab** — new home for all configuration
- **Cookie manager**
  - Import cookies.txt via file picker (copies into the app folder)
  - Live status showing file size and last-modified timestamp
  - Refresh / Delete / Open Folder buttons
  - Green "installed" indicator when cookies are present
- **Proxy support** — SOCKS5 / SOCKS4 / HTTP / HTTPS
  - Validated on save (must include a scheme)
  - Applies to single downloads, audio, and queue items
- **Speed limiter** — cap download bandwidth
  - Accepts `5M`, `500K`, `1.5G`, or raw bytes
  - Leave empty for unlimited
- **Concurrent downloads** — 1 to 4 parallel queue items
  - Dropdown in SETTINGS (default: 1)
  - Safe worker-pool with atomic item claiming
- **Auto-updater**
  - Checks GitHub Releases on launch
  - Prompts only when a newer tag exists
  - Opens the release page in your browser with one click
- **First-run wizard**
  - Detects missing FFmpeg and points to the download page
  - Flags missing cookies as optional
  - Only appears on first launch
- **Theme picker** — Dark, Light, Cyberpunk, Solarized
  - Applied on Save Settings — UI rebuilds in the new palette
- **Toast notifications**
  - Bottom-right popup when a download or queue finishes
  - Auto-dismiss in ~4 seconds, click to dismiss early
  - Toggle on/off in SETTINGS

### Changed
- `downloader.build_ydl_opts` and `build_audio_ydl_opts` accept a
  `net_opts` dict for proxy + rate limit
- `QueueManager.start` accepts a `concurrency` parameter
- All settings persist in `config.json` alongside window geometry
- `app.py` runs post-launch checks (wizard → update check)

### Added (new modules)
- `urlgrab/theme.py` — theme presets and live palette swapping
- `urlgrab/updater.py` — GitHub release version checker
- `urlgrab/wizard.py` — first-run setup dialog
- `urlgrab/notifier.py` — borderless toast popup

### Notes
- Auto-update only *notifies* — it never replaces files on disk
- Wizard appears once; a settings key marks it as completed
- All new features use the existing bundled `ffmpeg.exe` and yt-dlp

---

## [1.1.4FD] - 2024-XX-XX

**Feature-Dense release.** Four major features shipped together —
audio extraction, subtitles, thumbnails, and video trimming.

### Added
- **AUDIO tab** — extract MP3 audio from any supported site
  - Bitrate picker: 128 / 192 / 256 / 320 kbps (default: 192)
  - Standalone `.mp3` output, written to the current download folder
  - Reuses the main URL field — no separate input needed
  - Auto-recorded in HISTORY with quality marked "MP3"
- **Subtitle download** — checkbox on the FORMATS tab
  - Optional subtitle language field (default: `en`, comma-separated)
  - Saves `.srt` files next to the video
  - Grabs both manual and auto-generated subtitles
- **Thumbnail download** — checkbox on the FORMATS tab
  - Saves the video's thumbnail as a `.jpg` beside the file
- **Trim / clip** — checkbox on the FORMATS tab
  - Start + End time fields (HH:MM:SS)
  - Stream-copy trim via FFmpeg (fast, no re-encode)
  - Leave End empty to grab from start to the end of the video
- New module: `urlgrab/ui/audio_tab.py`
- New helpers in `urlgrab/downloader.py`:
  - `build_audio_ydl_opts()` — audio-only pipeline with FFmpegExtractAudio
  - `parse_timecode()` — accepts `HH:MM:SS`, `MM:SS`, or raw seconds
  - `build_ydl_opts()` extended with `subtitles`, `thumbnail`,
    `trim_start`, `trim_end` parameters

### Changed
- Notebook now has four tabs: FORMATS, HISTORY, BATCH, AUDIO
- FORMATS tab gained an **options row** below the formats table
- Subtitle / trim fields appear inline only when their checkbox is ticked

### Fixed
- Timecode parser tolerates empty strings and malformed input
- Trim download warns the user if the checkbox is enabled but both
  fields are blank

### Notes
- All four features run on the existing bundled `ffmpeg.exe`

---

## [1.1.3] - 2024-XX-XX

### Added
- **BATCH tab** — full download queue with playlist + multi-link support
  - Paste multiple URLs (one per line) → **Add URLs** to enqueue
  - **Load Playlist** expands a playlist URL into individual items
  - Sequential download queue — one item at a time
  - Live per-item progress in the queue table
  - **Start Queue** / **Stop** / **Clear Finished** controls
  - Right-click a queue row → Copy URL / Remove from Queue
  - Completed queue items land in HISTORY automatically
- New module: `urlgrab/queue.py` — thread-safe sequential queue
- New module: `urlgrab/ui/batch_tab.py` — the BATCH tab UI

### Changed
- `urlgrab/app.py` wires the new `BatchTabMixin` and `QueueManager` in
- The notebook now has three tabs: FORMATS, HISTORY, BATCH

### Fixed
- Queue updates throttled at 50 ms to prevent UI flooding
- Queue shutdown on window close is now graceful

---

## [1.1.2] - 2024-XX-XX

### Added
- Window geometry memory — position and size restore on next launch
- Output folder memory — last chosen folder restores on launch
  (only if the folder still exists)
- `config.json` file next to the app stores these settings

### Changed
- `choose_folder` now saves the config immediately
- Window close handler (`WM_DELETE_WINDOW`) saves config before exiting

---

## [1.1.1] - 2024-XX-XX

### Added
- **Paste** button next to the URL field — reads clipboard with one click
- Auto-paste on focus — clicking into an empty URL field fills it
  automatically if the clipboard contains a URL

### Changed
- Status bar now reports paste actions

---

## [1.1.0] - 2024-XX-XX

### Added
- **HISTORY tab** — last 50 downloads stored in `history.json`
  - Double-click a row to open its folder
  - Right-click a row → Open Folder / Copy Source URL / Remove from History
  - **Clear History** button with confirmation
- **Right-click context menu** on the FORMATS table:
  - Copy Video URL
  - Copy Format ID
  - Open in Browser
- Window icon loaded from `icon.ico` (bundled with PyInstaller)

### Changed
- FORMATS and HISTORY now live in tabs
- URL card and download footer stay visible across tabs

---

## [1.0.0] - 2024-XX-XX

### Added
- First public release
- Paste a video URL, fetch all available formats, download in any resolution
- 4K / 2K / FHD / HD / SD resolution labels
- MP4 and MKV output
- FFmpeg merge for high-quality video + audio
- Optional **aria2c** acceleration with 16 concurrent connections
- Parallel fragment downloads via yt-dlp
- Live progress bar with download speed
- Cookie support via `cookies.txt` for Instagram / Facebook
- Frozen-aware paths — works as a script or as a PyInstaller one-file exe
- Modern dark UI built with ttkbootstrap
