import os
import tkinter as tk
import webbrowser
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from .config import (
    COLORS,
    BASE_DIR,
    COOKIES_FILE,
    FFMPEG_DIR,
)


class FirstRunWizard(tk.Toplevel):
    def __init__(self, master, on_finish):
        super().__init__(master)
        self.on_finish = on_finish

        self.title("Welcome to URLGrab")
        self.configure(bg=COLORS["bg"])
        self.geometry("560x480")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._center_on_master(master)
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._skip)

    def _center_on_master(self, master):
        master.update_idletasks()
        px = master.winfo_rootx() + (master.winfo_width() - 560) // 2
        py = master.winfo_rooty() + (master.winfo_height() - 480) // 2
        self.geometry(f"560x480+{px}+{py}")

    def _build(self):
        root = tk.Frame(self, bg=COLORS["bg"])
        root.pack(fill=BOTH, expand=True, padx=26, pady=22)

        tk.Label(
            root, text="Welcome to URLGrab",
            bg=COLORS["bg"], fg=COLORS["text"],
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor=W)

        tk.Label(
            root,
            text="Quick setup — takes 10 seconds.",
            bg=COLORS["bg"], fg=COLORS["text_dim"],
            font=("Segoe UI", 10),
        ).pack(anchor=W, pady=(4, 18))

        # FFmpeg check
        self._status_row(
            root,
            "FFmpeg",
            "Required for merging HD video + audio",
            self._has_ffmpeg(),
            required=True,
        )

        # Cookies check
        self._status_row(
            root,
            "Cookies",
            "Optional — needed for Instagram / Facebook",
            self._has_cookies(),
            required=False,
        )

        # Footer
        footer = tk.Frame(root, bg=COLORS["bg"])
        footer.pack(side=BOTTOM, fill=X, pady=(20, 0))

        ttk.Button(
            footer,
            text="Continue",
            style="Success.TButton",
            command=self._finish,
        ).pack(side=RIGHT)

        ttk.Button(
            footer,
            text="Skip",
            style="Ghost.TButton",
            command=self._skip,
        ).pack(side=RIGHT, padx=(0, 8))

    def _status_row(self, parent, title, desc, ok, required):
        card = tk.Frame(
            parent,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(fill=X, pady=(0, 10))

        inner = tk.Frame(card, bg=COLORS["surface_2"])
        inner.pack(fill=X, padx=16, pady=12)

        icon = "✅" if ok else ("❌" if required else "⚠️")
        color = COLORS["success"] if ok else (
            COLORS["danger"] if required else COLORS["text_dim"]
        )

        tk.Label(
            inner, text=icon,
            bg=COLORS["surface_2"], fg=color,
            font=("Segoe UI", 14),
        ).pack(side=LEFT, padx=(0, 12))

        text_wrap = tk.Frame(inner, bg=COLORS["surface_2"])
        text_wrap.pack(side=LEFT, fill=X, expand=True)

        tk.Label(
            text_wrap, text=title,
            bg=COLORS["surface_2"], fg=COLORS["text"],
            font=("Segoe UI", 10, "bold"), anchor=W,
        ).pack(anchor=W)

        tk.Label(
            text_wrap, text=desc,
            bg=COLORS["surface_2"], fg=COLORS["text_dim"],
            font=("Segoe UI", 9), anchor=W,
        ).pack(anchor=W)

        if not ok:
            ttk.Button(
                inner,
                text="Get it",
                style="Ghost.TButton",
                command=self._open_ffmpeg if required else self._open_cookies_help,
            ).pack(side=RIGHT)

    def _has_ffmpeg(self):
        if getattr(os, "name", "") == "nt":
            return (
                os.path.isfile(os.path.join(FFMPEG_DIR, "ffmpeg.exe"))
                and os.path.isfile(os.path.join(FFMPEG_DIR, "ffprobe.exe"))
            )
        return (
            os.path.isfile(os.path.join(FFMPEG_DIR, "ffmpeg"))
            and os.path.isfile(os.path.join(FFMPEG_DIR, "ffprobe"))
        )

    def _has_cookies(self):
        return os.path.isfile(COOKIES_FILE)

    def _open_ffmpeg(self):
        webbrowser.open(
            "https://github.com/yt-dlp/FFmpeg-Builds/wiki/Latest"
        )

    def _open_cookies_help(self):
        messagebox.showinfo(
            "Cookies",
            "Open the SETTINGS tab inside URLGrab and use the cookie "
            "manager to import a cookies.txt file.\n\n"
            "You only need this for sites that require login.",
        )

    def _finish(self):
        try:
            self.on_finish()
        finally:
            self.destroy()

    def _skip(self):
        try:
            self.on_finish()
        finally:
            self.destroy()