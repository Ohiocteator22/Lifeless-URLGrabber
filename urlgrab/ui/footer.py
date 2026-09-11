import tkinter as tk
from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import COLORS


class FooterMixin:
    def _build_footer(self, parent):
        footer = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        footer.pack(fill=X)

        f_inner = tk.Frame(footer, bg=COLORS["surface"])
        f_inner.pack(fill=X, padx=18, pady=16)

        top_f = tk.Frame(f_inner, bg=COLORS["surface"])
        top_f.pack(fill=X, pady=(0, 12))

        ttk.Button(
            top_f,
            text="📁  Choose Folder",
            style="Ghost.TButton",
            command=self.choose_folder,
        ).pack(side=LEFT)

        tk.Label(
            top_f,
            textvariable=self.output_path,
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
            anchor=W,
        ).pack(side=LEFT, padx=14, fill=X, expand=True)

        bottom_f = tk.Frame(f_inner, bg=COLORS["surface"])
        bottom_f.pack(fill=X)

        self.download_btn = ttk.Button(
            bottom_f,
            text="⬇  Download",
            style="Success.TButton",
            command=self.download_selected,
        )
        self.download_btn.pack(side=LEFT)

        prog_wrap = tk.Frame(bottom_f, bg=COLORS["surface"])
        prog_wrap.pack(side=LEFT, fill=X, expand=True, padx=(18, 0))

        self.progress = ttk.Progressbar(
            prog_wrap,
            style="Modern.Horizontal.TProgressbar",
            mode="determinate",
            maximum=100,
        )
        self.progress.pack(fill=X, pady=(0, 6))

        tk.Label(
            prog_wrap,
            textvariable=self.status_var,
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
            anchor=W,
        ).pack(anchor=W)

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_path.get())
        if folder:
            self.output_path.set(folder)
            self._save_config()