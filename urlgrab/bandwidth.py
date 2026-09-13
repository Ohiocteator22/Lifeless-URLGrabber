import datetime
import platform
import subprocess
import threading
import time

from . import logger
from .config import parse_speed_limit


_wifi_cache = {"value": None, "at": 0.0}
_wifi_lock = threading.Lock()


def is_night_time(start_str, end_str):
    """Return True if now is within [start, end). Handles overnight wrap."""
    try:
        start = datetime.datetime.strptime(start_str, "%H:%M").time()
        end = datetime.datetime.strptime(end_str, "%H:%M").time()
    except Exception:
        return False

    now = datetime.datetime.now().time()
    if start <= end:
        return start <= now < end
    return now >= start or now < end


def is_wifi_connected():
    """Best-effort Wi-Fi detection. Returns True/False/None if unknown."""
    if platform.system() != "Windows":
        return None

    now = time.time()
    with _wifi_lock:
        if _wifi_cache["value"] is not None and now - _wifi_cache["at"] < 15:
            return _wifi_cache["value"]

    result = None
    try:
        flags = 0
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            flags = subprocess.CREATE_NO_WINDOW

        proc = subprocess.run(
            ["netsh", "interface", "show", "interface"],
            capture_output=True,
            text=True,
            timeout=4,
            creationflags=flags,
        )
        for line in proc.stdout.splitlines():
            low = line.lower()
            if "wi-fi" in low or "wireless" in low:
                if "connected" in low:
                    result = True
                    break
        if result is None:
            result = False
    except Exception:
        result = None

    with _wifi_lock:
        _wifi_cache["value"] = result
        _wifi_cache["at"] = now
    return result


def get_effective_limit(settings, for_queue=False):
    """Return the effective ratelimit in bytes/sec, or None for unlimited.
    Applies night mode and per-context rules from settings."""
    if not settings:
        return None

    # Night mode lifts the limit entirely
    if settings.get("bandwidth_night_mode"):
        start = settings.get("bandwidth_night_start", "02:00")
        end = settings.get("bandwidth_night_end", "08:00")
        if is_night_time(start, end):
            return None

    # Queue items can ignore the limit if apply_to_queue is off
    if for_queue and not settings.get("bandwidth_apply_to_queue", True):
        return None

    return parse_speed_limit(settings.get("speed_limit"))


def preflight_check(settings):
    """Return (ok, reason) before starting a download.
    Used to block Wi-Fi-only mode when not on Wi-Fi."""
    if not settings:
        return True, ""

    if settings.get("bandwidth_wifi_only"):
        status = is_wifi_connected()
        if status is False:
            return False, "Wi-Fi-only mode is on, but this PC isn't on Wi-Fi."
        if status is None:
            logger.append(
                "Wi-Fi-only check couldn't determine connection — allowing.",
                "WARNING",
            )

    return True, ""