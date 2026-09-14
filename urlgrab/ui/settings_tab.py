import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import (
    COLORS,
    COOKIES_FILE,
    DEFAULT_SETTINGS,
    human_filesize,
    parse_speed_limit,
)
from ..theme import THEMES
from .. import platform_utils


class SettingsTabMixin:
    def _build_settings_tab(self):
        tab = tk.Frame(self.notebook, bg=COLORS["surface"])
        self.notebook.add(tab, text="  SETTINGS  ")

        outer = tk.Frame(tab, bg=COLORS["surface"])
        outer.pack(fill=BOTH, expand=True)

        canvas = tk.Canvas(
            outer, bg=COLORS["surface"], highlightthickness=0, bd=0,
        )
        scrollbar = ttk.Scrollbar(
            outer, orient=VERTICAL, command=canvas.yview,
        )
        self._settings_frame = tk.Frame(canvas, bg=COLORS["surface"])

        self._settings_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            ),
        )
        canvas.create_window(
            (0, 0), window=self._settings_frame, anchor="nw",
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"),
        )

        parent = self._settings_frame
        pad = tk.Frame(parent, bg=COLORS["surface"])
        pad.pack(fill=BOTH, expand=True, padx=18, pady=18)

        self._build_cookie_section(pad)
        self._build_network_section(pad)
        self._build_bandwidth_section(pad)
        self._build_concurrency_section(pad)
        self._build_appearance_section(pad)
        self._build_system_section(pad)
        self._build_save_row(pad)

        self._current_theme = self.settings.get("theme", "Dark")
        self._refresh_cookie_status()

    def _build_save_row(self, parent):
        save_row = tk.Frame(parent, bg=COLORS["surface"])
        save_row.pack(fill=X, pady=(18, 0))

        self.save_settings_btn = tk.Button(
            save_row,
            text="Save Settings",
            bg=COLORS["success"],
            fg="#ffffff",
            activebackground=COLORS["success_hov"],
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=24,
            pady=10,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            command=self._save_settings,
        )
        self.save_settings_btn.pack(side=LEFT)

        self.settings_saved_var = tk.StringVar(value="")
        tk.Label(
            save_row,
            textvariable=self.settings_saved_var,
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT, padx=14)

    def _build_cookie_section(self, parent):
        card = tk.Frame(
            parent,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(fill=X)

        inner = tk.Frame(card, bg=COLORS["surface_2"])
        inner.pack(fill=X, padx=18, pady=16)

        tk.Label(
            inner,
            text="COOKIES",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W)

        tk.Label(
            inner,
            text=(
                "Some sites (Instagram, Facebook, private content) "
                "require you to be logged in. Export your browser "
                "cookies as cookies.txt and import them here."
            ),
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
            wraplength=760,
            justify=LEFT,
        ).pack(anchor=W, pady=(4, 12))

        status_row = tk.Frame(inner, bg=COLORS["surface_2"])
        status_row.pack(fill=X, pady=(0, 12))

        tk.Label(
            status_row,
            text="Status:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)

        self.cookie_status_var = tk.StringVar(value="—")
        self.cookie_status_label = tk.Label(
            status_row,
            textvariable=self.cookie_status_var,
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 10),
        )
        self.cookie_status_label.pack(side=LEFT, padx=(8, 0))

        btn_row = tk.Frame(inner, bg=COLORS["surface_2"])
        btn_row.pack(fill=X)

        ttk.Button(
            btn_row, text="Import cookies.txt", style="Accent.TButton",
            command=self._import_cookies,
        ).pack(side=LEFT, padx=(0, 8))

        ttk.Button(
            btn_row, text="Refresh", style="Ghost.TButton",
            command=self._refresh_cookie_status,
        ).pack(side=LEFT, padx=(0, 8))

        self.cookie_open_btn = ttk.Button(
            btn_row, text="Open Folder", style="Ghost.TButton",
            command=self._open_cookie_folder,
        )
        self.cookie_open_btn.pack(side=LEFT, padx=(0, 8))

        self.cookie_delete_btn = ttk.Button(
            btn_row, text="Delete", style="Ghost.TButton",
            command=self._delete_cookies,
        )
        self.cookie_delete_btn.pack(side=LEFT)

    def _refresh_cookie_status(self):
        if not os.path.isfile(COOKIES_FILE):
            self.cookie_status_var.set("Not installed")
            self.cookie_status_label.config(fg=COLORS["text_dim"])
            try:
                self.cookie_delete_btn.config(state="disabled")
            except Exception:
                pass
            return

        try:
            size = os.path.getsize(COOKIES_FILE)
            mtime = os.path.getmtime(COOKIES_FILE)
            when = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            self.cookie_status_var.set(
                f"Installed · {human_filesize(size)} · {when}"
            )
            self.cookie_status_label.config(fg=COLORS["success"])
            self.cookie_delete_btn.config(state="normal")
        except Exception:
            self.cookie_status_var.set("Installed")
            self.cookie_status_label.config(fg=COLORS["success"])

    def _import_cookies(self):
        path = filedialog.askopenfilename(
            title="Select cookies.txt",
            filetypes=[("Cookies file", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            shutil.copyfile(path, COOKIES_FILE)
        except Exception as e:
            messagebox.showerror("Error", f"Could not import cookies:\n{e}")
            return
        self._refresh_cookie_status()
        self._notify_cookies_status()
        self._set_status("cookies.txt imported.")

    def _delete_cookies(self):
        if not os.path.isfile(COOKIES_FILE):
            return
        if not messagebox.askyesno(
            "Delete cookies",
            "Remove cookies.txt? Instagram / Facebook downloads will "
            "stop working until you import it again.",
        ):
            return
        try:
            os.remove(COOKIES_FILE)
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete cookies:\n{e}")
            return
        self._refresh_cookie_status()
        self._set_status("cookies.txt removed.")

    def _open_cookie_folder(self):
        folder = os.path.dirname(COOKIES_FILE)
        if not platform_utils.open_in_file_manager(folder):
            messagebox.showerror("Error", "Could not open folder.")

    def _build_network_section(self, parent):
        card = tk.Frame(
            parent,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(fill=X, pady=(14, 0))

        inner = tk.Frame(card, bg=COLORS["surface_2"])
        inner.pack(fill=X, padx=18, pady=16)

        tk.Label(
            inner, text="NETWORK",
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 10))

        proxy_row = tk.Frame(inner, bg=COLORS["surface_2"])
        proxy_row.pack(fill=X, pady=(0, 10))

        tk.Label(
            proxy_row, text="Proxy:", bg=COLORS["surface_2"],
            fg=COLORS["text"], font=("Segoe UI", 10),
            width=14, anchor=W,
        ).pack(side=LEFT)

        self.proxy_var = tk.StringVar(value=self.settings.get("proxy", ""))
        ttk.Entry(
            proxy_row, textvariable=self.proxy_var,
            font=("Consolas", 10),
        ).pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

        tk.Label(
            proxy_row,
            text="socks5://host:port  or  http://host:port",
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT)

    def _build_bandwidth_section(self, parent):
        card = tk.Frame(
            parent,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(fill=X, pady=(14, 0))

        inner = tk.Frame(card, bg=COLORS["surface_2"])
        inner.pack(fill=X, padx=18, pady=16)

        tk.Label(
            inner, text="BANDWIDTH",
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 10))

        speed_row = tk.Frame(inner, bg=COLORS["surface_2"])
        speed_row.pack(fill=X, pady=(0, 10))

        tk.Label(
            speed_row, text="Global limit:",
            bg=COLORS["surface_2"], fg=COLORS["text"],
            font=("Segoe UI", 10), width=14, anchor=W,
        ).pack(side=LEFT)

        self.speed_var = tk.StringVar(
            value=self.settings.get("speed_limit", "")
        )
        ttk.Entry(
            speed_row, textvariable=self.speed_var,
            width=14, font=("Consolas", 10),
        ).pack(side=LEFT, padx=(0, 10))

        tk.Label(
            speed_row,
            text="e.g. 5M, 500K, 1.5G — empty = unlimited",
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT)

        self.bw_apply_queue_var = tk.BooleanVar(
            value=self.settings.get("bandwidth_apply_to_queue", True)
        )
        tk.Checkbutton(
            inner, text="Apply to queue downloads",
            variable=self.bw_apply_queue_var,
            bg=COLORS["surface_2"], fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0, highlightthickness=0,
        ).pack(anchor=W, pady=(0, 4))

        self.bw_wifi_var = tk.BooleanVar(
            value=self.settings.get("bandwidth_wifi_only", False)
        )
        tk.Checkbutton(
            inner, text="Only download when on Wi-Fi",
            variable=self.bw_wifi_var,
            bg=COLORS["surface_2"], fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0, highlightthickness=0,
        ).pack(anchor=W, pady=(0, 4))

        self.bw_pause_drop_var = tk.BooleanVar(
            value=self.settings.get("bandwidth_pause_on_drop", False)
        )
        tk.Checkbutton(
            inner, text="Pause queue when a download fails",
            variable=self.bw_pause_drop_var,
            bg=COLORS["surface_2"], fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0, highlightthickness=0,
        ).pack(anchor=W, pady=(0, 8))

        self.bw_night_var = tk.BooleanVar(
            value=self.settings.get("bandwidth_night_mode", False)
        )
        night_row = tk.Frame(inner, bg=COLORS["surface_2"])
        night_row.pack(fill=X)

        tk.Checkbutton(
            night_row, text="Night mode (no limit between):",
            variable=self.bw_night_var,
            bg=COLORS["surface_2"], fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0, highlightthickness=0,
        ).pack(side=LEFT)

        self.bw_night_start_var = tk.StringVar(
            value=self.settings.get("bandwidth_night_start", "02:00")
        )
        ttk.Entry(
            night_row, textvariable=self.bw_night_start_var,
            width=7, font=("Consolas", 10),
        ).pack(side=LEFT, padx=(8, 4))

        tk.Label(
            night_row, text="→",
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)

        self.bw_night_end_var = tk.StringVar(
            value=self.settings.get("bandwidth_night_end", "08:00")
        )
        ttk.Entry(
            night_row, textvariable=self.bw_night_end_var,
            width=7, font=("Consolas", 10),
        ).pack(side=LEFT, padx=(4, 0))

    def _build_concurrency_section(self, parent):
        card = tk.Frame(
            parent,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(fill=X, pady=(14, 0))

        inner = tk.Frame(card, bg=COLORS["surface_2"])
        inner.pack(fill=X, padx=18, pady=16)

        tk.Label(
            inner, text="BATCH CONCURRENCY",
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 10))

        row = tk.Frame(inner, bg=COLORS["surface_2"])
        row.pack(fill=X)

        tk.Label(
            row, text="Parallel downloads:",
            bg=COLORS["surface_2"], fg=COLORS["text"],
            font=("Segoe UI", 10), width=20, anchor=W,
        ).pack(side=LEFT)

        self.concurrency_var = tk.StringVar(
            value=str(self.settings.get("concurrent_downloads", 1))
        )
        ttk.Combobox(
            row, textvariable=self.concurrency_var,
            values=["1", "2", "3", "4"],
            state="readonly", width=6, font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(0, 14))

        tk.Label(
            row,
            text="Higher = faster but heavier on bandwidth.",
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT)

        retry_row = tk.Frame(inner, bg=COLORS["surface_2"])
        retry_row.pack(fill=X, pady=(10, 0))

        tk.Label(
            retry_row, text="Auto-retry failed:",
            bg=COLORS["surface_2"], fg=COLORS["text"],
            font=("Segoe UI", 10), width=20, anchor=W,
        ).pack(side=LEFT)

        self.retry_var = tk.StringVar(
            value=str(self.settings.get("queue_auto_retry", 2))
        )
        ttk.Combobox(
            retry_row, textvariable=self.retry_var,
            values=["0", "1", "2", "3", "5"],
            state="readonly", width=6, font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(0, 14))

        tk.Label(
            retry_row, text="times per item",
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT)

    def _build_appearance_section(self, parent):
        card = tk.Frame(
            parent,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(fill=X, pady=(14, 0))

        inner = tk.Frame(card, bg=COLORS["surface_2"])
        inner.pack(fill=X, padx=18, pady=16)

        tk.Label(
            inner, text="APPEARANCE",
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 10))

        theme_row = tk.Frame(inner, bg=COLORS["surface_2"])
        theme_row.pack(fill=X)

        tk.Label(
            theme_row, text="Theme:",
            bg=COLORS["surface_2"], fg=COLORS["text"],
            font=("Segoe UI", 10), width=14, anchor=W,
        ).pack(side=LEFT)

        self.theme_var = tk.StringVar(
            value=self.settings.get("theme", "Dark")
        )
        ttk.Combobox(
            theme_row, textvariable=self.theme_var,
            values=list(THEMES.keys()),
            state="readonly", width=14, font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(0, 14))

        tk.Label(
            theme_row,
            text="Applied on Save — UI rebuilds in the new style.",
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT)

        notif_row = tk.Frame(inner, bg=COLORS["surface_2"])
        notif_row.pack(fill=X, pady=(12, 0))

        self.notifications_var = tk.BooleanVar(
            value=self.settings.get("notifications", True)
        )
        tk.Checkbutton(
            notif_row,
            text="Show notification on download complete",
            variable=self.notifications_var,
            bg=COLORS["surface_2"], fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0, highlightthickness=0,
        ).pack(side=LEFT)

    def _build_system_section(self, parent):
        card = tk.Frame(
            parent,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(fill=X, pady=(14, 0))

        inner = tk.Frame(card, bg=COLORS["surface_2"])
        inner.pack(fill=X, padx=18, pady=16)

        tk.Label(
            inner, text="SYSTEM",
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 10))

        self.tray_var = tk.BooleanVar(
            value=self.settings.get("tray_on_close", True)
        )
        tk.Checkbutton(
            inner,
            text=(
                "Minimize to system tray on close "
                "(right-click tray icon to quit)"
            ),
            variable=self.tray_var,
            bg=COLORS["surface_2"], fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0, highlightthickness=0,
        ).pack(anchor=W)

    def _save_settings(self):
        proxy = self.proxy_var.get().strip()
        speed = self.speed_var.get().strip()

        if proxy and not (
            proxy.startswith("http://")
            or proxy.startswith("https://")
            or proxy.startswith("socks5://")
            or proxy.startswith("socks4://")
        ):
            messagebox.showerror(
                "Invalid proxy",
                "Proxy must start with http://, https://, socks5://, "
                "or socks4://",
            )
            return

        if speed and parse_speed_limit(speed) is None:
            messagebox.showerror(
                "Invalid speed limit",
                "Speed limit must look like 5M, 500K, or 1.5G.",
            )
            return

        try:
            concurrency = int(self.concurrency_var.get())
        except ValueError:
            concurrency = 1

        try:
            auto_retry = int(self.retry_var.get())
        except ValueError:
            auto_retry = 2

        new_theme = self.theme_var.get()

        try:
            self.save_settings_btn.config(text="Saving..")
        except Exception:
            pass

        self.settings = {
            "proxy": proxy,
            "speed_limit": speed,
            "concurrent_downloads": concurrency,
            "theme": new_theme,
            "notifications": self.notifications_var.get(),
            "tray_on_close": self.tray_var.get(),
            "first_run_complete": self.settings.get(
                "first_run_complete", True
            ),
            "bandwidth_apply_to_queue": self.bw_apply_queue_var.get(),
            "bandwidth_night_mode": self.bw_night_var.get(),
            "bandwidth_night_start": self.bw_night_start_var.get().strip() or "02:00",
            "bandwidth_night_end": self.bw_night_end_var.get().strip() or "08:00",
            "bandwidth_pause_on_drop": self.bw_pause_drop_var.get(),
            "bandwidth_wifi_only": self.bw_wifi_var.get(),
            "queue_auto_retry": auto_retry,
        }
        self.queue.auto_retry = auto_retry
        self._save_config()

        self.settings_saved_var.set("Saved..")
        self._set_status("Settings saved.")

        self.after(1500, self._reset_save_button)
        self.after(2500, lambda: self.settings_saved_var.set(""))

        if new_theme != self._current_theme:
            self._current_theme = new_theme
            self.apply_theme_live(new_theme)

    def _reset_save_button(self):
        try:
            self.save_settings_btn.config(text="Save Settings")
        except Exception:
            pass