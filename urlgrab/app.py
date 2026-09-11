import os
import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from .config import (
    BASE_DIR,
    COOKIES_FILE,
    COLORS,
    DEFAULT_GEOMETRY,
    MIN_SIZE,
    resolution_label,
)
from . import storage
from .queue import QueueManager
from .ui.styles import build_styles
from .ui.header import HeaderMixin
from .ui.formats_tab import FormatsTabMixin
from .ui.history_tab import HistoryTabMixin
from .ui.batch_tab import BatchTabMixin
from .ui.audio_tab import AudioTabMixin
from .ui.footer import FooterMixin


class URLGrabApp(
    HeaderMixin,
    FormatsTabMixin,
    HistoryTabMixin,
    BatchTabMixin,
    AudioTabMixin,
    FooterMixin,
    ttk.Window,
):
    def __init__(self):
        super().__init__(themename="darkly")

        self.config = storage.load_config()

        self.title("URLGrab")
        self.minsize(*MIN_SIZE)
        self.configure(bg=COLORS["bg"])

        self.video_info = None
        self.format_map = {}
        self.history = storage.load_history()
        self._current_record = None
        self._last_clipboard_check = ""
        self._queue_update_pending = False

        self.url_var = tk.StringVar()
        self.output_path = tk.StringVar(value=BASE_DIR)
        self.status_var = tk.StringVar(value="Ready")

        self.queue = QueueManager(
            on_update=self._queue_changed,
            on_item_done=self._queue_item_done,
        )

        self._restore_saved_state()
        self._set_window_icon()

        build_styles()

        self._build_ui()
        self._refresh_history_tree()
        self._notify_cookies_status()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # UI assembly
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = tk.Frame(self, bg=COLORS["bg"])
        root.pack(fill=BOTH, expand=True, padx=26, pady=22)

        self._build_header(root)

        self.notebook = ttk.Notebook(root, style="Modern.TNotebook")
        self.notebook.pack(fill=BOTH, expand=True, pady=(0, 14))

        self._build_formats_tab()
        self._build_history_tab()
        self._build_batch_tab()
        self._build_audio_tab()

        self._build_footer(root)

    # ------------------------------------------------------------------
    # Queue -> history bridge
    # ------------------------------------------------------------------
    def _queue_item_done(self, item):
        height = item.get("height")
        record = {
            "timestamp": item.get("timestamp", "—"),
            "title": item.get("title", "Unknown"),
            "url": item.get("url", ""),
            "quality": resolution_label(height) if height else "—",
            "resolution": f"{height}p" if height else "—",
            "container": item.get("container", "mp4"),
            "format_id": None,
            "output_dir": item.get("out_dir", ""),
        }
        self.after(0, lambda: self._add_to_history(record))

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    def _restore_saved_state(self):
        geo = self.config.get("window_geometry") or DEFAULT_GEOMETRY
        try:
            self.geometry(geo)
        except Exception:
            self.geometry(DEFAULT_GEOMETRY)

        folder = self.config.get("output_folder")
        if folder and os.path.isdir(folder):
            self.output_path.set(folder)

    def _save_config(self):
        cfg = dict(self.config)
        try:
            cfg["window_geometry"] = self.geometry()
        except Exception:
            pass
        cfg["output_folder"] = self.output_path.get()
        storage.save_config(cfg)

    def _on_close(self):
        try:
            self.queue.stop()
        except Exception:
            pass
        self._save_config()
        self.destroy()

    # ------------------------------------------------------------------
    # Window icon
    # ------------------------------------------------------------------
    def _set_window_icon(self):
        try:
            from .config import resource_path
            icon = resource_path("icon.ico")
            if os.path.isfile(icon):
                self.iconbitmap(icon)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------
    def _notify_cookies_status(self):
        if os.path.isfile(COOKIES_FILE):
            self._set_status("cookies.txt detected — Instagram/FB enabled.")

    def _cookie_opts(self):
        if os.path.isfile(COOKIES_FILE):
            return {"cookiefile": COOKIES_FILE}
        return {}

    def _set_status(self, text):
        self.status_var.set(text)


def main():
    app = URLGrabApp()
    app.mainloop()