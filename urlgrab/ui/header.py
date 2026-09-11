import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import COLORS, looks_like_url


class HeaderMixin:
    def _build_header(self, parent):
        header = tk.Frame(parent, bg=COLORS["bg"])
        header.pack(fill=X, pady=(0, 18))

        tk.Label(
            header,
            text="URLGrab",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor=W)
        tk.Label(
            header,
            text="Paste a link. Pick a quality. Done.",
            bg=COLORS["bg"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 10),
        ).pack(anchor=W, pady=(2, 0))

        url_card = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        url_card.pack(fill=X, pady=(0, 14))

        url_inner = tk.Frame(url_card, bg=COLORS["surface"])
        url_inner.pack(fill=X, padx=18, pady=18)

        tk.Label(
            url_inner,
            text="VIDEO URL",
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 8))

        url_row = tk.Frame(url_inner, bg=COLORS["surface"])
        url_row.pack(fill=X)

        self.url_entry = ttk.Entry(
            url_row,
            textvariable=self.url_var,
            style="Modern.TEntry",
            font=("Segoe UI", 10),
        )
        self.url_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        self.url_entry.bind("<Return>", lambda e: self.fetch_formats())
        self.url_entry.bind("<FocusIn>", self._on_url_focus)

        ttk.Button(
            url_row,
            text="📋  Paste",
            style="Ghost.TButton",
            command=self._paste_from_clipboard,
        ).pack(side=LEFT, padx=(0, 8))

        ttk.Button(
            url_row,
            text="Fetch",
            style="Accent.TButton",
            command=self.fetch_formats,
        ).pack(side=LEFT)

    def _get_clipboard_text(self):
        try:
            return self.clipboard_get().strip()
        except tk.TclError:
            return ""

    def _paste_from_clipboard(self):
        text = self._get_clipboard_text()
        if not text:
            self._set_status("Clipboard is empty.")
            return
        self.url_var.set(text)
        self.url_entry.icursor(END)
        self.url_entry.focus_set()
        if looks_like_url(text):
            self._set_status("Pasted from clipboard.")
        else:
            self._set_status("Pasted (doesn't look like a URL).")

    def _on_url_focus(self, event=None):
        if self.url_var.get().strip():
            return
        text = self._get_clipboard_text()
        if not text or not looks_like_url(text):
            return
        if text == self._last_clipboard_check:
            return
        self._last_clipboard_check = text
        self.url_var.set(text)
        self.url_entry.icursor(END)
        self._set_status("Auto-pasted URL from clipboard.")