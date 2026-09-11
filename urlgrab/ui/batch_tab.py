import threading
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import yt_dlp

from ..config import COLORS, looks_like_url, resolution_label
from ..queue import (
    QueueManager,
    STATUS_PENDING,
    STATUS_DOWNLOADING,
    STATUS_DONE,
    STATUS_ERROR,
    STATUS_CANCELLED,
)


STATUS_LABEL = {
    STATUS_PENDING:     "Pending",
    STATUS_DOWNLOADING: "Downloading…",
    STATUS_DONE:        "✅ Done",
    STATUS_ERROR:       "❌ Error",
    STATUS_CANCELLED:   "⏹ Cancelled",
}


class BatchTabMixin:
    def _build_batch_tab(self):
        tab = tk.Frame(self.notebook, bg=COLORS["surface"])
        self.notebook.add(tab, text="  BATCH  ")

        inner = tk.Frame(tab, bg=COLORS["surface"])
        inner.pack(fill=BOTH, expand=True, padx=18, pady=18)

        # ---------- URL input ----------
        tk.Label(
            inner,
            text="URLS OR PLAYLIST",
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
        text_wrap.pack(fill=X)

        self.batch_text = tk.Text(
            text_wrap,
            height=5,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="white",
            relief="flat",
            bd=0,
            font=("Consolas", 10),
            padx=12,
            pady=10,
            wrap="none",
        )
        self.batch_text.pack(fill=X)

        btn_row = tk.Frame(inner, bg=COLORS["surface"])
        btn_row.pack(fill=X, pady=(10, 16))

        ttk.Button(
            btn_row,
            text="📥  Add URLs",
            style="Accent.TButton",
            command=self._batch_add_urls,
        ).pack(side=LEFT)

        ttk.Button(
            btn_row,
            text="📃  Load Playlist",
            style="Ghost.TButton",
            command=self._batch_load_playlist,
        ).pack(side=LEFT, padx=8)

        ttk.Button(
            btn_row,
            text="🧹  Clear Input",
            style="Ghost.TButton",
            command=lambda: self.batch_text.delete("1.0", tk.END),
        ).pack(side=LEFT)

        # ---------- Queue ----------
        tk.Label(
            inner,
            text="QUEUE",
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 8))

        queue_wrap = tk.Frame(inner, bg=COLORS["surface"])
        queue_wrap.pack(fill=BOTH, expand=True)

        cols = ("n", "title", "resolution", "status", "progress")
        self.queue_tree = ttk.Treeview(
            queue_wrap,
            columns=cols,
            show="headings",
            style="Modern.Treeview",
            selectmode="browse",
        )
        headings = {
            "n":          ("#",           40),
            "title":      ("Title",      420),
            "resolution": ("Quality",     90),
            "status":     ("Status",     140),
            "progress":   ("Progress",   100),
        }
        for c, (text, width) in headings.items():
            self.queue_tree.heading(c, text=text, anchor=W)
            self.queue_tree.column(
                c, width=width, anchor=W, stretch=(c == "title"),
            )

        vsb = ttk.Scrollbar(
            queue_wrap, orient=VERTICAL, command=self.queue_tree.yview,
        )
        self.queue_tree.configure(yscrollcommand=vsb.set)
        self.queue_tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)

        self.queue_menu = tk.Menu(
            self, tearoff=0,
            bg=COLORS["surface_2"], fg=COLORS["text"],
            activebackground=COLORS["accent"], activeforeground="white",
            borderwidth=0, font=("Segoe UI", 10),
        )
        self.queue_menu.add_command(
            label="Copy URL", command=self._queue_copy_url,
        )
        self.queue_menu.add_separator()
        self.queue_menu.add_command(
            label="Remove from Queue", command=self._queue_remove,
        )
        self.queue_tree.bind("<Button-3>", self._show_queue_menu)

        # ---------- Queue footer ----------
        qfooter = tk.Frame(inner, bg=COLORS["surface"])
        qfooter.pack(fill=X, pady=(12, 0))

        self.queue_start_btn = ttk.Button(
            qfooter,
            text="▶  Start Queue",
            style="Success.TButton",
            command=self._queue_start,
        )
        self.queue_start_btn.pack(side=LEFT)

        self.queue_stop_btn = ttk.Button(
            qfooter,
            text="⏹  Stop",
            style="Ghost.TButton",
            command=self._queue_stop,
        )
        self.queue_stop_btn.pack(side=LEFT, padx=8)

        ttk.Button(
            qfooter,
            text="🗑  Clear Finished",
            style="Ghost.TButton",
            command=self._queue_clear_done,
        ).pack(side=LEFT)

        self.queue_status_var = tk.StringVar(value="Queue empty.")
        tk.Label(
            qfooter,
            textvariable=self.queue_status_var,
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=RIGHT)

    # ------------------------------------------------------------------
    # Add URLs
    # ------------------------------------------------------------------
    def _batch_collect_urls(self):
        raw = self.batch_text.get("1.0", tk.END)
        lines = [ln.strip() for ln in raw.splitlines()]
        return [ln for ln in lines if looks_like_url(ln)]

    def _batch_add_urls(self):
        urls = self._batch_collect_urls()
        if not urls:
            messagebox.showinfo(
                "No URLs",
                "Paste one or more URLs into the box first.",
            )
            return
        for u in urls:
            self.queue.add(u, out_dir=self.output_path.get())
        self.batch_text.delete("1.0", tk.END)
        self._set_status(f"Added {len(urls)} URL(s) to queue.")

    # ------------------------------------------------------------------
    # Playlist
    # ------------------------------------------------------------------
    def _batch_load_playlist(self):
        raw = self.batch_text.get("1.0", tk.END)
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if not lines:
            messagebox.showinfo(
                "No URL",
                "Paste a playlist URL into the box first.",
            )
            return
        playlist_url = lines[0]
        self._set_status("Loading playlist…")

        threading.Thread(
            target=self._batch_load_playlist_thread,
            args=(playlist_url,),
            daemon=True,
        ).start()

    def _batch_load_playlist_thread(self, url):
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "noplaylist": False,
            **self._cookie_opts(),
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            self.after(0, lambda: self._playlist_error(str(e)))
            return

        entries = info.get("entries") or []
        collected = []
        for entry in entries:
            if not entry:
                continue
            video_url = entry.get("webpage_url") or entry.get("url")
            if video_url and not video_url.startswith("http"):
                video_url = f"https://www.youtube.com/watch?v={video_url}"
            if not video_url:
                continue
            collected.append((video_url, entry.get("title") or "Unknown"))

        self.after(0, lambda: self._playlist_loaded(collected))

    def _playlist_loaded(self, collected):
        if not collected:
            self._set_status("No videos found in playlist.")
            return
        for url, title in collected:
            self.queue.add(url, title=title, out_dir=self.output_path.get())
        self.batch_text.delete("1.0", tk.END)
        self._set_status(f"Loaded {len(collected)} video(s) from playlist.")

    def _playlist_error(self, err):
        self._set_status(f"Playlist error: {err[:80]}")
        messagebox.showerror("Playlist Error", err)

    # ------------------------------------------------------------------
    # Queue control
    # ------------------------------------------------------------------
    def _queue_start(self):
        if not self.queue.items:
            self._set_status("Queue is empty.")
            return
        if self.queue.is_running():
            self._set_status("Queue already running.")
            return
        self.queue.start(
            cookie_opts=self._cookie_opts(),
            default_out_dir=self.output_path.get(),
            default_height=1080,
        )
        self._set_status("Queue started.")

    def _queue_stop(self):
        if not self.queue.is_running():
            return
        self.queue.stop()
        self._set_status("Stopping queue…")

    def _queue_clear_done(self):
        self.queue.clear_done()

    # ------------------------------------------------------------------
    # Queue refresh (throttled, marshalled to main thread)
    # ------------------------------------------------------------------
    def _queue_changed(self):
        if self._queue_update_pending:
            return
        self._queue_update_pending = True
        self.after(50, self._do_queue_update)

    def _do_queue_update(self):
        self._queue_update_pending = False
        self._refresh_queue_tree()

    def _refresh_queue_tree(self):
        for row in self.queue_tree.get_children():
            self.queue_tree.delete(row)

        for i, item in enumerate(self.queue.items):
            title = item.get("title", "Unknown")
            if len(title) > 60:
                title = title[:57] + "…"

            height = item.get("height")
            res = f"{height}p" if height else "—"
            status = STATUS_LABEL.get(item["status"], item["status"])
            pct = item.get("progress", 0)
            prog = f"{pct:.0f}%"

            self.queue_tree.insert(
                "", END, iid=item["id"],
                values=(i + 1, title, res, status, prog),
            )

        total = len(self.queue.items)
        done = sum(1 for i in self.queue.items if i["status"] == STATUS_DONE)
        err = sum(1 for i in self.queue.items if i["status"] == STATUS_ERROR)
        running = self.queue.is_running()

        if total == 0:
            self.queue_status_var.set("Queue empty.")
        else:
            self.queue_status_var.set(
                f"{done}/{total} done"
                + (f" · {err} failed" if err else "")
                + (" · running" if running else "")
            )

        if running:
            self.queue_start_btn.config(state="disabled")
            self.queue_stop_btn.config(state="normal")
        else:
            self.queue_start_btn.config(state="normal")
            self.queue_stop_btn.config(state="disabled")

    # ------------------------------------------------------------------
    # Queue context menu
    # ------------------------------------------------------------------
    def _show_queue_menu(self, event):
        row = self.queue_tree.identify_row(event.y)
        if not row:
            return
        self.queue_tree.selection_set(row)
        try:
            self.queue_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.queue_menu.grab_release()

    def _selected_queue_item(self):
        sel = self.queue_tree.selection()
        if not sel:
            return None
        item_id = sel[0]
        for item in self.queue.items:
            if item["id"] == item_id:
                return item
        return None

    def _queue_copy_url(self):
        item = self._selected_queue_item()
        if not item:
            return
        self.clipboard_clear()
        self.clipboard_append(item["url"])
        self._set_status("Copied queue URL.")

    def _queue_remove(self):
        item = self._selected_queue_item()
        if not item:
            return
        self.queue.remove(item["id"])