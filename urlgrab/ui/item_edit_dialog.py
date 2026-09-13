import tkinter as tk
from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import COLORS


HEIGHT_OPTIONS = ["Auto", "480", "720", "1080", "1440", "2160"]
CONTAINER_OPTIONS = ["mp4", "mkv", "webm"]


class ItemEditDialog(tk.Toplevel):
    def __init__(self, master, item, on_save):
        super().__init__(master)
        self.item = dict(item)
        self.on_save = on_save

        self.title("Edit Queue Item")
        self.configure(bg=COLORS["bg"])
        self.geometry("520x420")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._center(master)
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _center(self, master):
        master.update_idletasks()
        px = master.winfo_rootx() + (master.winfo_width() - 520) // 2
        py = master.winfo_rooty() + (master.winfo_height() - 420) // 2
        self.geometry(f"520x420+{px}+{py}")

    def _build(self):
        root = tk.Frame(self, bg=COLORS["bg"])
        root.pack(fill=BOTH, expand=True, padx=20, pady=20)

        tk.Label(
            root,
            text="Edit Item",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor=W)

        tk.Label(
            root,
            text=(self.item.get("title") or "Unknown")[:70],
            bg=COLORS["bg"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 10),
        ).pack(anchor=W, pady=(2, 16))

        form = tk.Frame(root, bg=COLORS["bg"])
        form.pack(fill=X)

        # Priority
        row = tk.Frame(form, bg=COLORS["bg"])
        row.pack(fill=X, pady=(0, 8))
        tk.Label(
            row, text="Priority",
            bg=COLORS["bg"], fg=COLORS["text"],
            font=("Segoe UI", 10), width=14, anchor=W,
        ).pack(side=LEFT)
        self.priority_var = tk.StringVar(
            value=str(self.item.get("priority", 0))
        )
        ttk.Entry(
            row, textvariable=self.priority_var, width=10,
            font=("Segoe UI", 10),
        ).pack(side=LEFT)
        tk.Label(
            row, text="higher = downloaded first",
            bg=COLORS["bg"], fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT, padx=(10, 0))

        # Max height
        row = tk.Frame(form, bg=COLORS["bg"])
        row.pack(fill=X, pady=(0, 8))
        tk.Label(
            row, text="Max height",
            bg=COLORS["bg"], fg=COLORS["text"],
            font=("Segoe UI", 10), width=14, anchor=W,
        ).pack(side=LEFT)
        current_h = self.item.get("manual_height")
        self.height_var = tk.StringVar(
            value=str(current_h) if current_h else "Auto"
        )
        ttk.Combobox(
            row, textvariable=self.height_var, values=HEIGHT_OPTIONS,
            state="readonly", width=10, font=("Segoe UI", 10),
        ).pack(side=LEFT)

        # Container
        row = tk.Frame(form, bg=COLORS["bg"])
        row.pack(fill=X, pady=(0, 8))
        tk.Label(
            row, text="Container",
            bg=COLORS["bg"], fg=COLORS["text"],
            font=("Segoe UI", 10), width=14, anchor=W,
        ).pack(side=LEFT)
        self.container_var = tk.StringVar(
            value=self.item.get("container", "mp4")
        )
        ttk.Combobox(
            row, textvariable=self.container_var,
            values=CONTAINER_OPTIONS, state="readonly", width=10,
            font=("Segoe UI", 10),
        ).pack(side=LEFT)

        # Output folder
        row = tk.Frame(form, bg=COLORS["bg"])
        row.pack(fill=X, pady=(0, 8))
        tk.Label(
            row, text="Output folder",
            bg=COLORS["bg"], fg=COLORS["text"],
            font=("Segoe UI", 10), width=14, anchor=W,
        ).pack(side=LEFT)
        self.out_var = tk.StringVar(value=self.item.get("out_dir") or "")
        ttk.Entry(
            row, textvariable=self.out_var, font=("Segoe UI", 10),
        ).pack(side=LEFT, fill=X, expand=True, padx=(0, 6))
        ttk.Button(
            row, text="…", style="Ghost.TButton", width=3,
            command=self._pick_folder,
        ).pack(side=LEFT)

        tk.Label(
            root,
            text=(
                "Empty output folder = use the main download folder.\n"
                "Auto height = use the queue's default (usually 1080p)."
            ),
            bg=COLORS["bg"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
            justify=LEFT,
        ).pack(anchor=W, pady=(14, 0))

        footer = tk.Frame(root, bg=COLORS["bg"])
        footer.pack(side=BOTTOM, fill=X, pady=(16, 0))

        ttk.Button(
            footer, text="Cancel", style="Ghost.TButton",
            command=self.destroy,
        ).pack(side=RIGHT, padx=(8, 0))

        ttk.Button(
            footer, text="Save", style="Success.TButton",
            command=self._save,
        ).pack(side=RIGHT)

    def _pick_folder(self):
        folder = filedialog.askdirectory(
            initialdir=self.out_var.get() or None
        )
        if folder:
            self.out_var.set(folder)

    def _save(self):
        try:
            priority = int(self.priority_var.get() or 0)
        except ValueError:
            priority = 0

        h = self.height_var.get()
        manual_height = None if h == "Auto" else int(h)

        self.on_save({
            "priority": priority,
            "manual_height": manual_height,
            "container": self.container_var.get() or "mp4",
            "out_dir": self.out_var.get().strip() or None,
        })
        self.destroy()