import tkinter as tk

from .config import COLORS


class Toast:
    """Lightweight, borderless popup in the bottom-right of the screen."""

    def __init__(self, master, title, message, duration_ms=4200):
        self.master = master
        self.duration_ms = duration_ms

        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=COLORS["accent"])

        outer = tk.Frame(self.win, bg=COLORS["accent"])
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        inner = tk.Frame(outer, bg=COLORS["surface_2"])
        inner.pack(fill="both", expand=True)

        tk.Label(
            inner,
            text=title,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 2))

        tk.Label(
            inner,
            text=message,
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
            anchor="w",
            wraplength=280,
            justify="left",
        ).pack(fill="x", padx=14, pady=(0, 12))

        self.win.update_idletasks()
        w = 320
        h = self.win.winfo_reqheight()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x = sw - w - 24
        y = sh - h - 60
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        self.win.bind("<Button-1>", lambda e: self._dismiss())
        for child in (inner, outer):
            child.bind("<Button-1>", lambda e: self._dismiss())

        self.win.after(self.duration_ms, self._dismiss)

    def _dismiss(self):
        try:
            self.win.destroy()
        except Exception:
            pass


def notify(master, title, message):
    try:
        Toast(master, title, message)
    except Exception:
        pass