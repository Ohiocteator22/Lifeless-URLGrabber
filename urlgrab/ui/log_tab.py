import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import COLORS
from .. import logger


class LogTabMixin:
    def _build_log_tab(self):
        tab = tk.Frame(self.notebook, bg=COLORS["surface"])
        self.notebook.add(tab, text="  LOG  ")

        inner = tk.Frame(tab, bg=COLORS["surface"])
        inner.pack(fill=BOTH, expand=True, padx=18, pady=18)

        tk.Label(
            inner,
            text="ACTIVITY LOG",
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 8))

        text_wrap = tk.Frame(
            inner,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        text_wrap.pack(fill=BOTH, expand=True)

        self.log_text = tk.Text(
            text_wrap,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="white",
            relief="flat",
            bd=0,
            font=("Consolas", 9),
            padx=12,
            pady=10,
            wrap="word",
            state="disabled",
        )
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)

        vsb = ttk.Scrollbar(
            text_wrap, orient=VERTICAL, command=self.log_text.yview,
        )
        self.log_text.configure(yscrollcommand=vsb.set)
        vsb.pack(side=RIGHT, fill=Y)

        self.log_text.tag_configure("INFO", foreground=COLORS["text"])
        self.log_text.tag_configure("DEBUG", foreground=COLORS["text_dim"])
        self.log_text.tag_configure("STDERR", foreground=COLORS["text_dim"])
        self.log_text.tag_configure("WARNING", foreground="#f5a623")
        self.log_text.tag_configure("ERROR", foreground=COLORS["danger"])
        self.log_text.tag_configure("CRITICAL", foreground=COLORS["danger"])

        btn_row = tk.Frame(inner, bg=COLORS["surface"])
        btn_row.pack(fill=X, pady=(12, 0))

        ttk.Button(
            btn_row,
            text="📋  Copy All",
            style="Accent.TButton",
            command=self._log_copy_all,
        ).pack(side=LEFT)

        ttk.Button(
            btn_row,
            text="💾  Save to File",
            style="Ghost.TButton",
            command=self._log_save,
        ).pack(side=LEFT, padx=8)

        ttk.Button(
            btn_row,
            text="🧹  Clear",
            style="Ghost.TButton",
            command=self._log_clear,
        ).pack(side=LEFT)

        logger.subscribe(self._log_append)
        for line in logger.get_lines():
            self._log_append(line)

    def _log_append(self, line):
        def _do():
            try:
                if not self.log_text.winfo_exists():
                    return
                self.log_text.configure(state="normal")
                self.log_text.insert(END, f"[{line['time']}] ", "DEBUG")
                self.log_text.insert(
                    END, f"{line['level']:7s} ", line["level"]
                )
                self.log_text.insert(
                    END, f"{line['message']}\n", line["level"]
                )
                self.log_text.see(END)
                self.log_text.configure(state="disabled")
            except Exception:
                pass
        try:
            self.after(0, _do)
        except Exception:
            pass

    def _log_copy_all(self):
        lines = logger.get_lines()
        text = "\n".join(
            f"[{l['time']}] {l['level']:7s} {l['message']}" for l in lines
        )
        self.clipboard_clear()
        self.clipboard_append(text)
        self._set_status("Log copied to clipboard.")

    def _log_save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
            initialfile="urlgrab_log.txt",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                for l in logger.get_lines():
                    f.write(
                        f"[{l['time']}] {l['level']:7s} {l['message']}\n"
                    )
        except Exception as e:
            messagebox.showerror("Error", f"Could not save log:\n{e}")
            return
        self._set_status(f"Log saved to {path}")

    def _log_clear(self):
        logger.clear()
        try:
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", END)
            self.log_text.configure(state="disabled")
        except Exception:
            pass