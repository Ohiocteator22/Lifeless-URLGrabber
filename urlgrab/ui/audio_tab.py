import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import COLORS
from .. import downloader


BITRATES = ["128", "192", "256", "320"]
DEFAULT_BITRATE = "192"


class AudioTabMixin:
    def _build_audio_tab(self):
        tab = tk.Frame(self.notebook, bg=COLORS["surface"])
        self.notebook.add(tab, text="  AUDIO  ")

        inner = tk.Frame(tab, bg=COLORS["surface"])
        inner.pack(fill=BOTH, expand=True, padx=18, pady=18)

        # ---------- Intro ----------
        tk.Label(
            inner,
            text="EXTRACT AUDIO (MP3)",
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 8))

        tk.Label(
            inner,
            text=(
                "Paste a URL into the field at the top, pick a bitrate, "
                "and click Extract. The result is a standalone .mp3 file."
            ),
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 10),
            wraplength=760,
            justify=LEFT,
        ).pack(anchor=W, pady=(0, 22))

        # ---------- Options card ----------
        card = tk.Frame(
            inner,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.pack(fill=X)

        card_inner = tk.Frame(card, bg=COLORS["surface_2"])
        card_inner.pack(fill=X, padx=18, pady=18)

        row = tk.Frame(card_inner, bg=COLORS["surface_2"])
        row.pack(fill=X)

        tk.Label(
            row,
            text="Output bitrate:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)

        self.audio_bitrate_var = tk.StringVar(value=DEFAULT_BITRATE)
        bitrate_box = ttk.Combobox(
            row,
            textvariable=self.audio_bitrate_var,
            values=BITRATES,
            state="readonly",
            width=8,
            font=("Segoe UI", 10),
        )
        bitrate_box.pack(side=LEFT, padx=(10, 4))

        tk.Label(
            row,
            text="kbps",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)

        # ---------- Action row ----------
        action = tk.Frame(inner, bg=COLORS["surface"])
        action.pack(fill=X, pady=(22, 0))

        self.audio_btn = ttk.Button(
            action,
            text="🎵  Extract MP3",
            style="Success.TButton",
            command=self._audio_download,
        )
        self.audio_btn.pack(side=LEFT)

        tk.Label(
            action,
            text=(
                "Note: The MP3 is written to the folder shown at the bottom. "
                "The button uses the URL from the main field above."
            ),
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT, padx=14)

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------
    def _audio_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return

        bitrate = self.audio_bitrate_var.get()
        out_dir = self.output_path.get()

        self._audio_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "title": "Unknown",
            "url": url,
            "quality": "MP3",
            "resolution": f"{bitrate} kbps",
            "container": "mp3",
            "format_id": None,
            "output_dir": out_dir,
        }

        self.audio_btn.config(state="disabled", text="⏳  Starting…")
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        self._set_status(f"Extracting audio at {bitrate} kbps…")

        threading.Thread(
            target=self._audio_thread,
            args=(url, bitrate, out_dir),
            daemon=True,
        ).start()

    def _audio_thread(self, url, bitrate, out_dir):
        ydl_opts = downloader.build_audio_ydl_opts(
            out_dir=out_dir,
            bitrate=bitrate,
            cookie_opts=self._cookie_opts(),
            progress_hook=self._progress_hook,
            net_opts=self._net_opts(),
        )
        try:
            downloader.download(url, ydl_opts)
            self.after(0, lambda: self._audio_done(True, None))
        except Exception as e:
            self.after(0, lambda: self._audio_done(False, str(e)))

    def _audio_done(self, success, err):
        try:
            self.progress.stop()
        except Exception:
            pass
        self.progress.configure(mode="determinate")
        self.audio_btn.config(state="normal", text="🎵  Extract MP3")

        if success:
            self.progress["value"] = 100
            self._set_status("✅ MP3 ready")
            if getattr(self, "_audio_record", None):
                self._add_to_history(self._audio_record)
                self._audio_record = None
            messagebox.showinfo("Success", "MP3 extracted!")
        else:
            self.progress["value"] = 0
            low = (err or "").lower()
            if "login" in low or "sign in" in low or "cookie" in low:
                self._set_status("Login required — add cookies.txt")
                messagebox.showerror(
                    "Login Required",
                    "This site needs you to be logged in.\n\n"
                    "Drop a cookies.txt file next to this app and try again.",
                )
            else:
                self._set_status("❌ MP3 extract failed")
                messagebox.showerror(
                    "Error",
                    f"Audio extraction failed:\n{err}",
                )