import os
import webbrowser
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import COLORS
from .. import storage


class HistoryTabMixin:
    def _build_history_tab(self):
        tab = tk.Frame(self.notebook, bg=COLORS["surface"])
        self.notebook.add(tab, text="  HISTORY  ")

        inner = tk.Frame(tab, bg=COLORS["surface"])
        inner.pack(fill=BOTH, expand=True, padx=18, pady=18)

        tree_wrap = tk.Frame(inner, bg=COLORS["surface"])
        tree_wrap.pack(fill=BOTH, expand=True)

        cols = ("date", "title", "quality", "resolution", "container", "folder")
        self.history_tree = ttk.Treeview(
            tree_wrap,
            columns=cols,
            show="headings",
            style="Modern.Treeview",
            selectmode="browse",
        )
        headings = {
            "date":       ("Date",       140),
            "title":      ("Title",      340),
            "quality":    ("Quality",     90),
            "resolution": ("Resolution", 100),
            "container":  ("Container",   95),
            "folder":     ("Folder",     240),
        }
        for c, (text, width) in headings.items():
            self.history_tree.heading(c, text=text, anchor=W)
            self.history_tree.column(
                c,
                width=width,
                anchor=W,
                stretch=(c == "title"),
            )

        vsb = ttk.Scrollbar(
            tree_wrap,
            orient=VERTICAL,
            command=self.history_tree.yview,
        )
        self.history_tree.configure(yscrollcommand=vsb.set)
        self.history_tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)
        self.history_tree.bind(
            "<Double-1>", lambda e: self._open_history_folder()
        )

        bottom = tk.Frame(inner, bg=COLORS["surface"])
        bottom.pack(fill=X, pady=(12, 0))

        ttk.Button(
            bottom,
            text="🗑  Clear History",
            style="Ghost.TButton",
            command=self._clear_history,
        ).pack(side=LEFT)

        tk.Label(
            bottom,
            text="Double-click a row to open its folder.",
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT, padx=14)

        self.history_menu = tk.Menu(
            self,
            tearoff=0,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            activebackground=COLORS["accent"],
            activeforeground="white",
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        self.history_menu.add_command(
            label="Open Folder",
            command=self._open_history_folder,
        )
        self.history_menu.add_command(
            label="Copy Source URL",
            command=self._copy_history_url,
        )
        self.history_menu.add_separator()
        self.history_menu.add_command(
            label="Remove from History",
            command=self._remove_history_entry,
        )
        self.history_tree.bind("<Button-3>", self._show_history_menu)

    # ------------------------------------------------------------------
    # Data flow
    # ------------------------------------------------------------------
    def _add_to_history(self, record):
        self.history.insert(0, record)
        self.history = self.history[:50]
        storage.save_history(self.history)
        self._refresh_history_tree()

    def _refresh_history_tree(self):
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)

        for i, r in enumerate(self.history):
            title = r.get("title", "Unknown")
            if len(title) > 60:
                title = title[:57] + "…"
            folder = r.get("output_dir", "")
            if len(folder) > 40:
                folder = "…" + folder[-37:]

            self.history_tree.insert(
                "",
                END,
                iid=str(i),
                values=(
                    r.get("timestamp", "—"),
                    title,
                    r.get("quality", "—"),
                    r.get("resolution", "—"),
                    f".{r.get('container', 'mp4')}",
                    folder,
                ),
            )

    def _clear_history(self):
        if not self.history:
            return
        if not messagebox.askyesno(
            "Clear History",
            "Remove all download history entries?\n\n"
            "The files themselves won't be deleted.",
        ):
            return
        self.history = []
        storage.save_history(self.history)
        self._refresh_history_tree()

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------
    def _show_history_menu(self, event):
        row = self.history_tree.identify_row(event.y)
        if not row:
            return
        self.history_tree.selection_set(row)
        try:
            self.history_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.history_menu.grab_release()

    def _selected_history_record(self):
        sel = self.history_tree.selection()
        if not sel:
            return None
        try:
            idx = int(sel[0])
        except ValueError:
            return None
        if 0 <= idx < len(self.history):
            return idx, self.history[idx]
        return None

    def _open_history_folder(self):
        picked = self._selected_history_record()
        if not picked:
            return
        _, record = picked
        folder = record.get("output_dir", "")
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Folder no longer exists.")
            return
        try:
            os.startfile(folder)
        except AttributeError:
            webbrowser.open(f"file://{folder}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")

    def _copy_history_url(self):
        picked = self._selected_history_record()
        if not picked:
            return
        _, record = picked
        self.clipboard_clear()
        self.clipboard_append(record.get("url", ""))
        self._set_status("Copied source URL to clipboard.")

    def _remove_history_entry(self):
        picked = self._selected_history_record()
        if not picked:
            return
        idx, _ = picked
        del self.history[idx]
        storage.save_history(self.history)
        self._refresh_history_tree()