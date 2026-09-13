import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from . import __version__, GITHUB_OWNER, GITHUB_REPO
from .config import (
    BASE_DIR,
    COOKIES_FILE,
    COLORS,
    DEFAULT_GEOMETRY,
    DEFAULT_SETTINGS,
    MIN_SIZE,
    looks_like_url,
    parse_speed_limit,
    resolution_label,
)
from . import storage
from . import logger
from . import profiles as profiles_mod
from .queue import QueueManager
from .theme import apply_theme
from .updater import check_for_update
from .wizard import FirstRunWizard
from .notifier import notify
from . import tray
from .ui.styles import build_styles
from .ui.header import HeaderMixin
from .ui.formats_tab import FormatsTabMixin
from .ui.history_tab import HistoryTabMixin
from .ui.batch_tab import BatchTabMixin
from .ui.audio_tab import AudioTabMixin
from .ui.settings_tab import SettingsTabMixin
from .ui.log_tab import LogTabMixin
from .ui.footer import FooterMixin


try:
    from tkinterdnd2 import TkinterDnD, DND_FILES, DND_TEXT
    HAS_DND = True
except ImportError:
    HAS_DND = False
    DND_FILES = DND_TEXT = None

    class _DnDStub:
        def drop_target_register(self, *a, **k):
            pass

        def dnd_bind(self, *a, **k):
            pass

    class TkinterDnD:
        DnDWrapper = _DnDStub

        @staticmethod
        def _require(root):
            return None


class URLGrabApp(
    HeaderMixin,
    FormatsTabMixin,
    HistoryTabMixin,
    BatchTabMixin,
    AudioTabMixin,
    SettingsTabMixin,
    LogTabMixin,
    FooterMixin,
    TkinterDnD.DnDWrapper,
    ttk.Window,
):
    def __init__(self):
        self.config = storage.load_config()
        self.settings = dict(DEFAULT_SETTINGS)
        for key, default in DEFAULT_SETTINGS.items():
            self.settings[key] = self.config.get(key, default)

        theme_name = self.settings.get("theme", "Dark")
        ttk_name = apply_theme(theme_name)

        super().__init__(themename=ttk_name)

        if HAS_DND:
            try:
                self.TkdndVersion = TkinterDnD._require(self)
            except Exception:
                logger.append("DnD init failed", "WARNING")

        self.title("URLGrab")
        self.minsize(*MIN_SIZE)
        self.configure(bg=COLORS["bg"])

        self.video_info = None
        self.format_map = {}
        self.history = storage.load_history()
        self.profiles = profiles_mod.load_profiles()
        self._current_record = None
        self._last_clipboard_check = ""
        self._queue_update_pending = False
        self._tray_started = False
        self._quitting = False

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

        self._setup_dnd()
        self._setup_tray()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(300, self._post_launch_checks)

        logger.append(f"URLGrab v{__version__} started")

    # ------------------------------------------------------------------
    # Post-launch: wizard + updater
    # ------------------------------------------------------------------
    def _post_launch_checks(self):
        if not self.settings.get("first_run_complete"):
            FirstRunWizard(self, on_finish=self._mark_first_run_done)
            return
        self._check_updates_async()

    def _mark_first_run_done(self):
        self.settings["first_run_complete"] = True
        self._save_config()

    def _check_updates_async(self):
        threading.Thread(
            target=self._check_updates_thread, daemon=True
        ).start()

    def _check_updates_thread(self):
        result = check_for_update(
            current_version=__version__,
            owner=GITHUB_OWNER,
            repo=GITHUB_REPO,
        )
        if result and result.get("has_update"):
            self.after(0, lambda: self._prompt_update(result))

    def _prompt_update(self, info):
        tag = info["latest_tag"]
        yes = messagebox.askyesno(
            "Update available",
            f"URLGrab {tag} is available.\n"
            f"You're running v{__version__}.\n\n"
            "Open the release page to download it?",
        )
        if yes and info.get("url"):
            import webbrowser
            webbrowser.open(info["url"])

    # ------------------------------------------------------------------
    # Drag and drop
    # ------------------------------------------------------------------
    def _setup_dnd(self):
        if not HAS_DND:
            return
        try:
            self.drop_target_register(DND_TEXT, DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception as e:
            logger.append(f"DnD setup failed: {e}", "WARNING")

    def _on_drop(self, event):
        raw = getattr(event, "data", "") or ""
        url = self._extract_url_from_drop(raw)
        if not url:
            self._set_status("Dropped item isn't a URL.")
            return
        self.deiconify()
        self.lift()
        self.url_var.set(url)
        self._set_status("URL dropped — fetching…")
        logger.append(f"Dropped URL: {url}")
        self.fetch_formats()

    @staticmethod
    def _extract_url_from_drop(raw):
        if not raw:
            return None
        text = raw.strip()
        if text.startswith("{") and text.endswith("}"):
            text = text[1:-1]
        if " " in text and not text.startswith("http"):
            for token in text.split():
                t = token.strip("{}")
                if looks_like_url(t):
                    return t
        if looks_like_url(text):
            return text
        return None

    # ------------------------------------------------------------------
    # System tray
    # ------------------------------------------------------------------
    def _setup_tray(self):
        if not tray.is_available():
            logger.append(
                "System tray unavailable (pystray missing)", "WARNING"
            )
            return
        ok = tray.start(
            app=self,
            on_show=self._restore_from_tray,
            on_new_download=self._tray_new_download,
            on_quit=self._tray_quit,
        )
        self._tray_started = bool(ok)
        if ok:
            logger.append("System tray started")

    def _minimize_to_tray(self):
        if not self._tray_started:
            return False
        try:
            self.withdraw()
            logger.append("Minimized to tray")
            self._notify("URLGrab", "Still running in the system tray.")
            return True
        except Exception:
            return False

    def _restore_from_tray(self):
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _tray_new_download(self):
        self._restore_from_tray()
        try:
            self.url_var.set("")
            self.url_entry.focus_set()
        except Exception:
            pass
        self._set_status("Ready — paste or drop a URL.")

    def _tray_quit(self):
        self._quitting = True
        self._on_close()

    # ------------------------------------------------------------------
    # Theme switching
    # ------------------------------------------------------------------
    def apply_theme_live(self, theme_name):
        ttk_name = apply_theme(theme_name)
        try:
            self.style.theme_use(ttk_name)
        except Exception:
            pass

        build_styles()

        for child in list(self.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass

        self.configure(bg=COLORS["bg"])
        self._build_ui()
        self._refresh_history_tree()

        self.settings["theme"] = theme_name
        self._save_config()

    # ------------------------------------------------------------------
    # Notification helper
    # ------------------------------------------------------------------
    def _notify(self, title, message):
        if not self.settings.get("notifications", True):
            return
        notify(self, title, message)

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
        self._build_log_tab()
        self._build_settings_tab()

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
        for key, value in self.settings.items():
            cfg[key] = value
        storage.save_config(cfg)

    def _on_close(self):
        if (
            self._tray_started
            and not self._quitting
            and self.settings.get("tray_on_close", True)
        ):
            if self._minimize_to_tray():
                return

        try:
            self.queue.stop()
        except Exception:
            pass

        try:
            logger.unsubscribe(self._log_append)
        except Exception:
            pass

        tray.stop()

        self._save_config()
        self.destroy()

    # ------------------------------------------------------------------
    # Window icon
    # ------------------------------------------------------------------
    def _set_window_icon(self):
        try:
            candidates = []

            if hasattr(sys, "_MEIPASS"):
                candidates.append(os.path.join(sys._MEIPASS, "icon.ico"))

            candidates.append(os.path.join(BASE_DIR, "icon.ico"))

            from .config import resource_path
            candidates.append(resource_path("icon.ico"))

            for icon in candidates:
                if os.path.isfile(icon):
                    self.iconbitmap(icon)
                    return
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------
    def _notify_cookies_status(self):
        if os.path.isfile(COOKIES_FILE):
            self._set_status(
                "cookies.txt detected — Instagram/FB enabled."
            )

    def _cookie_opts(self):
        if os.path.isfile(COOKIES_FILE):
            return {"cookiefile": COOKIES_FILE}
        return {}

    def _net_opts(self):
        opts = {}
        proxy = (self.settings.get("proxy") or "").strip()
        if proxy:
            opts["proxy"] = proxy
        speed = parse_speed_limit(self.settings.get("speed_limit"))
        if speed:
            opts["ratelimit"] = speed
        return opts

    def _concurrency(self):
        try:
            return int(self.settings.get("concurrent_downloads", 1))
        except Exception:
            return 1

    def _set_status(self, text):
        self.status_var.set(text)


def main():
    logger.install()
    logger.install_excepthook()
    app = URLGrabApp()
    app.mainloop()