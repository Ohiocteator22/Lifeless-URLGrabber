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


class SettingsTabMixin:
    def _build_settings_tab(self):
        tab = tk.Frame(self.notebook, bg=COLORS["surface"])
        self.notebook.add(tab, text="  SETTINGS  ")

        outer = tk.Frame(tab, bg=COLORS["surface"])
        outer.pack(fill=BOTH, expand=True, padx=18, pady=18)

        # ---------- Cookie manager ----------
        self._build_cookie_section(outer)

        # ---------- Network settings ----------
        self._build_network_section(outer)

        # ---------- Concurrency ----------
        self._build_concurrency_section(outer)

        # ---------- Save row ----------
        save_row = tk.Frame(outer, bg=COLORS["surface"])
        save_row.pack(fill=X, pady=(18, 0))

        ttk.Button(
            save_row,
            text="💾  Save Settings",
            style="Success.TButton",
            command=self._save_settings,
        ).pack(side=LEFT)

        self.settings_saved_var = tk.StringVar(value="")
        tk.Label(
            save_row,
            textvariable=self.settings_saved_var,
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT, padx=14)

        self._refresh_cookie_status()

    # ------------------------------------------------------------------
    # Cookie manager
    # ------------------------------------------------------------------
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
            btn_row,
            text="📥  Import cookies.txt",
            style="Accent.TButton",
            command=self._import_cookies,
        ).pack(side=LEFT, padx=(0, 8))

        ttk.Button(
            btn_row,
            text="🔄  Refresh",
            style="Ghost.TButton",
            command=self._refresh_cookie_status,
        ).pack(side=LEFT, padx=(0, 8))

        self.cookie_open_btn = ttk.Button(
            btn_row,
            text="📂  Open Folder",
            style="Ghost.TButton",
            command=self._open_cookie_folder,
        )
        self.cookie_open_btn.pack(side=LEFT, padx=(0, 8))

        self.cookie_delete_btn = ttk.Button(
            btn_row,
            text="🗑  Delete",
            style="Ghost.TButton",
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
            filetypes=[
                ("Cookies file", "*.txt"),
                ("All files", "*.*"),
            ],
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
        try:
            os.startfile(folder)
        except AttributeError:
            import webbrowser
            webbrowser.open(f"file://{folder}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")

    # ------------------------------------------------------------------
    # Network settings
    # ------------------------------------------------------------------
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
            inner,
            text="NETWORK",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 10))

        # Proxy
        proxy_row = tk.Frame(inner, bg=COLORS["surface_2"])
        proxy_row.pack(fill=X, pady=(0, 10))

        tk.Label(
            proxy_row,
            text="Proxy:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
            width=14,
            anchor=W,
        ).pack(side=LEFT)

        self.proxy_var = tk.StringVar(
            value=self.settings.get("proxy", "")
        )
        ttk.Entry(
            proxy_row,
            textvariable=self.proxy_var,
            font=("Consolas", 10),
        ).pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

        tk.Label(
            proxy_row,
            text="socks5://host:port  or  http://host:port",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT)

        # Speed limiter
        speed_row = tk.Frame(inner, bg=COLORS["surface_2"])
        speed_row.pack(fill=X)

        tk.Label(
            speed_row,
            text="Speed limit:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
            width=14,
            anchor=W,
        ).pack(side=LEFT)

        self.speed_var = tk.StringVar(
            value=self.settings.get("speed_limit", "")
        )
        ttk.Entry(
            speed_row,
            textvariable=self.speed_var,
            width=14,
            font=("Consolas", 10),
        ).pack(side=LEFT, padx=(0, 10))

        tk.Label(
            speed_row,
            text="e.g. 5M, 500K, 1.5G — leave empty for unlimited",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT)

    # ------------------------------------------------------------------
    # Concurrency
    # ------------------------------------------------------------------
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
            inner,
            text="BATCH CONCURRENCY",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 10))

        row = tk.Frame(inner, bg=COLORS["surface_2"])
        row.pack(fill=X)

        tk.Label(
            row,
            text="Parallel downloads:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
            width=20,
            anchor=W,
        ).pack(side=LEFT)

        self.concurrency_var = tk.StringVar(
            value=str(self.settings.get("concurrent_downloads", 1))
        )
        ttk.Combobox(
            row,
            textvariable=self.concurrency_var,
            values=["1", "2", "3", "4"],
            state="readonly",
            width=6,
            font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(0, 14))

        tk.Label(
            row,
            text=(
                "Higher = faster but heavier on bandwidth. "
                "Start with 2 or 3 on a fast connection."
            ),
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def _save_settings(self):
        proxy = self.proxy_var.get().strip()
        speed = self.speed_var.get().strip()

        # Validate proxy format (basic)
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

        # Validate speed limit
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

        self.settings = {
            "proxy": proxy,
            "speed_limit": speed,
            "concurrent_downloads": concurrency,
        }
        self._save_config()
        self.settings_saved_var.set("✅ Saved")
        self.after(2500, lambda: self.settings_saved_var.set(""))
        self._set_status("Settings saved.")