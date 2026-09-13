import logging
import sys
import threading
from collections import deque
from datetime import datetime


MAX_LOG_LINES = 500

_LOG_BUFFER = deque(maxlen=MAX_LOG_LINES)
_LOCK = threading.Lock()
_LISTENERS = []


class _BufferHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
        except Exception:
            return
        append(msg, record.levelname)


def append(message, level="INFO"):
    line = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": str(message),
    }
    with _LOCK:
        _LOG_BUFFER.append(line)
        listeners = list(_LISTENERS)
    for cb in listeners:
        try:
            cb(line)
        except Exception:
            pass


def get_lines():
    with _LOCK:
        return list(_LOG_BUFFER)


def clear():
    with _LOCK:
        _LOG_BUFFER.clear()


def subscribe(callback):
    with _LOCK:
        _LISTENERS.append(callback)


def unsubscribe(callback):
    with _LOCK:
        if callback in _LISTENERS:
            _LISTENERS.remove(callback)


class _StderrRedirector:
    def __init__(self, original):
        self.original = original

    def write(self, text):
        if text and text.strip():
            append(text.rstrip(), level="STDERR")
        if self.original:
            try:
                self.original.write(text)
            except Exception:
                pass

    def flush(self):
        if self.original:
            try:
                self.original.flush()
            except Exception:
                pass


def install():
    """Attach logging capture + stderr redirect. Idempotent."""
    if getattr(install, "_installed", False):
        return
    install._installed = True

    handler = _BufferHandler()
    handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    sys.stderr = _StderrRedirector(sys.stderr)


def _excepthook(exc_type, exc_value, exc_tb):
    import traceback
    append(
        "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        level="ERROR",
    )


def install_excepthook():
    sys.excepthook = _excepthook