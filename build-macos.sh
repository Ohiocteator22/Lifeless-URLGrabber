#!/usr/bin/env bash
#
# URLGrab macOS build script
# Usage:  bash build-macos.sh
#
set -e

echo ""
echo "🍎 URLGrab — macOS build"
echo "========================"
echo ""

# --- 1. Python dependencies ---------------------------------------------------
echo "→ Installing Python dependencies…"
pip3 install --user --quiet -r requirements.txt
pip3 install --user --quiet pyinstaller

# --- 2. FFmpeg + FFprobe ------------------------------------------------------
echo "→ Downloading FFmpeg…"
curl -sL -o ffmpeg.zip  "https://evermeet.cx/ffmpeg/getrelease/zip"
curl -sL -o ffprobe.zip "https://evermeet.cx/ffprobe/getrelease/zip"
unzip -o -q ffmpeg.zip  && rm ffmpeg.zip
unzip -o -q ffprobe.zip && rm ffprobe.zip
chmod +x ffmpeg ffprobe

# --- 3. aria2c (via Homebrew, optional) ---------------------------------------
if command -v brew >/dev/null 2>&1; then
    echo "→ Installing aria2c via Homebrew…"
    brew install aria2 >/dev/null 2>&1 || true
    if command -v aria2c >/dev/null 2>&1; then
        cp "$(command -v aria2c)" ./aria2c
        chmod +x aria2c
    fi
else
    echo "→ Homebrew not found — skipping aria2c (downloads will still work)"
fi

# --- 4. Convert icon.ico → icon.icns ------------------------------------------
if [ -f icon.ico ]; then
    echo "→ Converting icon…"
    rm -rf icon.iconset
    mkdir -p icon.iconset
    python3 - <<'PYEOF'
from PIL import Image
img = Image.open("icon.ico")
for s in (16, 32, 64, 128, 256, 512):
    img.resize((s, s)).save(f"icon.iconset/icon_{s}x{s}.png")
    img.resize((s * 2, s * 2)).save(f"icon.iconset/icon_{s}x{s}@2x.png")
PYEOF
    iconutil -c icns icon.iconset -o icon.icns
    rm -rf icon.iconset
fi

# --- 5. Build -----------------------------------------------------------------
echo "→ Building URLGrab.app…"
ICON_FLAG=""
[ -f icon.icns ] && ICON_FLAG="--icon icon.icns --add-data icon.icns:."

BIN_FLAGS=""
[ -f ffmpeg ]  && BIN_FLAGS="$BIN_FLAGS --add-binary ffmpeg:."
[ -f ffprobe ] && BIN_FLAGS="$BIN_FLAGS --add-binary ffprobe:."
[ -f aria2c ]  && BIN_FLAGS="$BIN_FLAGS --add-binary aria2c:."

pyinstaller \
    --noconfirm --windowed --clean \
    --name "URLGrab" \
    $ICON_FLAG \
    $BIN_FLAGS \
    --collect-all yt_dlp \
    --collect-all ttkbootstrap \
    --collect-all tkinterdnd2 \
    --collect-all pystray \
    --collect-all PIL \
    URLGrab.py

echo ""
echo "✅ Done!"
echo ""
echo "Your app is at:  dist/URLGrab.app"
echo ""
echo "First launch: right-click the app → Open → Open"
echo "or run:       xattr -cr dist/URLGrab.app"
echo ""