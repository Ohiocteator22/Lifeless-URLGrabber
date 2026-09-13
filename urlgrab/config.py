import os
import sys


def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)


def user_path(relative):
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)


BASE_DIR = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

FFMPEG_DIR = resource_path("") if getattr(sys, "frozen", False) else BASE_DIR

ARIA2C_PATH = resource_path("aria2c.exe")
if not os.path.isfile(ARIA2C_PATH):
    alt = os.path.join(BASE_DIR, "aria2c.exe")
    ARIA2C_PATH = alt if os.path.isfile(alt) else None

COOKIES_FILE = user_path("cookies.txt")
HISTORY_FILE = user_path("history.json")
CONFIG_FILE  = user_path("config.json")
PROFILES_FILE = user_path("profiles.json")


MAX_HISTORY = 50
DEFAULT_GEOMETRY = "980x760"
MIN_SIZE = (820, 620)


COLORS = {
    "bg":          "#0d0f14",
    "surface":     "#151821",
    "surface_2":   "#1b1f2b",
    "border":      "#232838",
    "text":        "#e7e9f0",
    "text_dim":    "#7f869c",
    "accent":      "#7c5cff",
    "accent_hov":  "#8f74ff",
    "success":     "#10b981",
    "success_hov": "#14c98f",
    "danger":      "#ef4444",
    "danger_hov":  "#f56565",
}


DEFAULT_SETTINGS = {
    "proxy": "",
    "speed_limit": "",
    "concurrent_downloads": 1,
    "theme": "Dark",
    "notifications": True,
    "first_run_complete": False,
    "tray_on_close": True,
}


def looks_like_url(text):
    if not text:
        return False
    text = text.strip()
    if len(text) < 8 or " " in text:
        return False
    return text.startswith("http://") or text.startswith("https://")


def resolution_label(height):
    if height >= 2160:
        return "4K"
    if height >= 1440:
        return "2K"
    if height >= 1080:
        return "FHD"
    if height >= 720:
        return "HD"
    if height >= 480:
        return "SD"
    return "LOW"


def parse_speed_limit(text):
    if not text:
        return None
    text = str(text).strip().upper()
    if not text:
        return None
    try:
        if text.endswith("K"):
            return int(float(text[:-1]) * 1024)
        if text.endswith("M"):
            return int(float(text[:-1]) * 1024 * 1024)
        if text.endswith("G"):
            return int(float(text[:-1]) * 1024 * 1024 * 1024)
        return int(float(text))
    except ValueError:
        return None


def human_filesize(num_bytes):
    if not num_bytes:
        return "—"
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"