import datetime
import threading
import time

from . import logger
from .config import parse_speed_limit
from . import platform_utils


_wifi_cache = {"value": None, "at": 0.0}
_wifi_lock = threading.Lock()


def is_night_time(start_str, end_str):
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
    now = time.time()
    with _wifi_lock:
        if _wifi_cache["value"] is not None and now - _wifi_cache["at"] < 15:
            return _wifi_cache["value"]

    result = platform_utils.get_wifi_status()

    with _wifi_lock:
        _wifi_cache["value"] = result
        _wifi_cache["at"] = now
    return result


def get_effective_limit(settings, for_queue=False):
    if not settings:
        return None

    if settings.get("bandwidth_night_mode"):
        start = settings.get("bandwidth_night_start", "02:00")
        end = settings.get("bandwidth_night_end", "08:00")
        if is_night_time(start, end):
            return None

    if for_queue and not settings.get("bandwidth_apply_to_queue", True):
        return None

    return parse_speed_limit(settings.get("speed_limit"))


def preflight_check(settings):
    if not settings:
        return True, ""

    if settings.get("bandwidth_wifi_only"):
        status = is_wifi_connected()
        if status is False:
            return False, "Wi-Fi-only mode is on, but this PC isn't on Wi-Fi."
        if status is None:
            logger.append(
                "Wi-Fi-only check couldn't determine connection - allowing.",
                "WARNING",
            )

    return True, ""