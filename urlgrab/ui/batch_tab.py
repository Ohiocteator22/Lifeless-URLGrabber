import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import yt_dlp

from ..config import COLORS, looks_like_url, resolution_label
from ..queue import (
    STATUS_PENDING,
    STATUS_DOWNLOADING,
    STATUS_DONE,
    STATUS_ERROR,
    STATUS_CANCELLED,
)
from .. import bandwidth
from .. import platform_utils
from .item_edit_dialog import ItemEditDialog


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
            height=4,
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
        btn_row.pack(fill=X, pady=(10, 12))

        ttk.Button(
            btn_row, text="📥  Add URLs",
            style="Accent.TButton", command=self._batch_add_urls,
        ).pack(side=LEFT)

        ttk.Button(
            btn_row, text="📃  Load Playlist",
            style="Ghost.TButton", command=self._batch_load_playlist,
        ).pack(side=LEFT, padx=8)

        ttk.Button(
            btn_row, text="🧹  Clear Input",
            style="Ghost.TButton",
            command=lambda: self.batch_text.delete("1.0", tk.END),
        ).pack(side=LEFT)

        tk.Label(
            inner,
            text="QUEUE",
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 8))

        queue_wrap = tk.Frame(inner, bg=COLORS["surface"])
        queue_wrap.pack(fill=BOTH, expand=True)

        cols = ("n", "p", "title", "resolution", "status", "progress")
        self.queue_tree = ttk.Treeview(
            queue_wrap,
            columns=cols,
            show="headings",
            style="Modern.Treeview",
            selectmode="browse",
        )
        headings = {
            "n":          ("#",            35),
            "p":          ("P",            35),
            "title":      ("Title",       360),
            "resolution": ("Quality",      85),
            "status":     ("Status",      140),
            "progress":   ("Progress",     95),
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
        self.queue_tree.bind(
            "<Double-1>", lambda e: self._queue_edit()
        )

        self.queue_menu = tk.Menu(
            self, tearoff=0,
            bg=COLORS["surface_2"], fg=COLORS["text"],
            activebackground=COLORS["accent"], activeforeground="white",
            borderwidth=0, font=("Segoe UI", 10),
        )
        self.queue_menu.add_command(
            label="Edit…", command=self._queue_edit,
        )
        self.queue_menu.add_separator()
        self.queue_menu.add_command(
            label="Pause", command=self._queue_pause_item,
        )
        self.queue_menu.add_command(
            label="Resume", command=self._queue_resume_item,
        )
        self.queue_menu.add_command(
            label="Retry", command=self._queue_retry,
        )
        self.queue_menu.add_separator()
        self.queue_menu.add_command(
            label="Move Up", command=lambda: self._queue_move(-1),
        )
        self.queue_menu.add_command(
            label="Move Down", command=lambda: self._queue_move(1),
        )
        self.queue_menu.add_separator()
        self.queue_menu.add_command(
            label="Copy URL", command=self._queue_copy_url,
        )
        self.queue_menu.add_command(
            label="Open Folder", command=self._queue_open_folder,
        )
        self.queue_menu.add_separator()
        self.queue_menu.add_command(
            label="Remove from Queue", command=self._queue_remove,
        )
        self.queue_tree.bind("<Button-3>", self._show_queue_menu)

        qfooter = tk.Frame(inner, bg=COLORS["surface"])
        qfooter.pack(fill=X, pady=(12, 0))

        self.queue_start_btn = ttk.Button(
            qfooter, text="▶  Start",
            style="Success.TButton", command=self._queue_start,
        )
        self.queue_start_btn.pack(side=LEFT)

        self.queue_pause_btn = ttk.Button(
            qfooter, text="⏸  Pause",
            style="Ghost.TButton", command=self._queue_pause_all,
        )
        self.queue_pause_btn.pack(side=LEFT, padx=6)

        self.queue_stop_btn = ttk.Button(
            qfooter, text="⏹  Stop",
            style="Ghost.TButton", command=self._queue_stop,
        )
        self.queue_stop_btn.pack(side=LEFT)

        ttk.Button(
            qfooter, text="🔄  Retry Failed",
            style="Ghost.TButton", command=self._queue_retry_all,
        ).pack(side=LEFT, padx=6)

        ttk.Button(
            qfooter, text="🗑  Clear Finished",
            style="Ghost.TButton", command=self._queue_clear_done,
        ).pack(side=LEFT)

        ttk.Button(
            qfooter, text="📤  Export",
            style="Ghost.TButton", command=self._queue_export,
        ).pack(side=RIGHT, padx=(6, 0))

        ttk.Button(
            qfooter, text="📥  Import",
            style="Ghost.TButton", command=self._queue_import,
        ).pack(side=RIGHT)

        self.queue_status_var = tk.StringVar(value="Queue empty.")
        tk.Label(
            qfooter,
            textvariable=self.queue_status_var,
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=RIGHT, padx=14)

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

    def _batch_load_playlist(self):
        raw = self.batch_text.get("1.0", tk.END)
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if not lines:
            messagebox.showinfo(
                "No URL",
                "Paste a playlist URL into the box first.",
            )
            return
        self._set_status("Loading playlist…")

        threading.Thread(
            target=self._batch_load_playlist_thread,
            args=(lines[0],),
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

    def _queue_start(self):
        if not self.queue.items:
            self._set_status("Queue is empty.")
            return
        if self.queue.is_running():
            self._set_status("Queue already running.")
            return

        ok, reason = bandwidth.preflight_check(self.settings)
        if not ok:
            messagebox.showwarning("Network check failed", reason)
            self._set_status(reason)
            return

        self.queue.start(
            cookie_opts=self._cookie_opts(),
            default_out_dir=self.output_path.get(),
            default_height=1080,
            concurrency=self._concurrency(),
            net_opts=self._net_opts(for_queue=True),
            auto_retry=int(self.settings.get("queue_auto_retry", 2)),
        )
        self._set_status("Queue started.")

    def _queue_pause_all(self):
        if self.queue.is_paused():
            self.queue.resume_all()
            self._set_status("Queue resumed.")
        else:
            self.queue.pause_all()
            self._set_status("Queue paused (current items keep running).")

    def _queue_stop(self):
        if not self.queue.is_running():
            return
        self.queue.stop()
        self._set_status("Stopping queue…")

    def _queue_clear_done(self):
        self.queue.clear_done()

    def _queue_retry_all(self):
        self.queue.retry_all_failed()
        self._set_status("Retrying failed items.")

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
        return self.queue.find(sel[0])

    def _queue_copy_url(self):
        item = self._selected_queue_item()
        if not item:
            return
        self.clipboard_clear()
        self.clipboard_append(item["url"])
        self._set_status("Copied queue URL.")

    def _queue_open_folder(self):
        item = self._selected_queue_item()
        if not item:
            return
        folder = item.get("out_dir") or self.output_path.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Folder no longer exists.")
            return
        if not platform_utils.open_in_file_manager(folder):
            messagebox.showerror("Error", "Could not open folder.")

    def _queue_remove(self):
        item = self._selected_queue_item()
        if not item:
            return
        self.queue.remove(item["id"])

    def _queue_pause_item(self):
        item = self._selected_queue_item()
        if not item:
            return
        self.queue.pause_item(item["id"])
        self._set_status(f"Paused: {item.get('title', 'item')}")

    def _queue_resume_item(self):
        item = self._selected_queue_item()
        if not item:
            return
        self.queue.resume_item(item["id"])
        self._set_status(f"Resumed: {item.get('title', 'item')}")

    def _queue_retry(self):
        item = self._selected_queue_item()
        if not item:
            return
        self.queue.retry_item(item["id"])
        self._set_status(f"Retrying: {item.get('title', 'item')}")

    def _queue_move(self, direction):
        item = self._selected_queue_item()
        if not item:
            return
        self.queue.reorder(item["id"], direction)
        self.queue_tree.selection_set(item["id"])

    def _queue_edit(self):
        item = self._selected_queue_item()
        if not item:
            return

        def _on_save(updates):
            self.queue.update_item(item["id"], updates)
            self._set_status(f"Updated: {item.get('title', 'item')}")

        ItemEditDialog(self, item, _on_save)

    def _queue_export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Queue file", "*.json"), ("All files", "*.*")],
            initialfile="urlgrab_queue.json",
        )
        if not path:
            return
        if self.queue.export_to(path):
            self._set_status(f"Queue exported to {os.path.basename(path)}")
        else:
            messagebox.showerror("Export failed", "Could not write the file.")

    def _queue_import(self):
        path = filedialog.askopenfilename(
            filetypes=[("Queue file", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        merge = messagebox.askyesno(
            "Import queue",
            "Add to the existing queue?\n\n"
            "Yes = append\nNo = replace current queue",
        )
        if self.queue.import_from(path, merge=merge):
            self._set_status("Queue imported.")
        else:
            messagebox.showerror("Import failed", "Could not read the file.")

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
            if item.get("paused"):
                title = "⏸ " + title
            if int(item.get("priority", 0)) > 0:
                title = f"[{item['priority']}] " + title
            if len(title) > 60:
                title = title[:57] + "…"

            h = item.get("manual_height") or item.get("height")
            res = f"{h}p" if h else "—"
            status = STATUS_LABEL.get(item["status"], item["status"])
            pct = item.get("progress", 0)
            prog = f"{pct:.0f}%"
            prio = str(item.get("priority", 0))

            self.queue_tree.insert(
                "", END, iid=item["id"],
                values=(i + 1, prio, title, res, status, prog),
            )

        total = len(self.queue.items)
        done = sum(1 for i in self.queue.items if i["status"] == STATUS_DONE)
        err = sum(1 for i in self.queue.items if i["status"] == STATUS_ERROR)
        pending = sum(
            1 for i in self.queue.items if i["status"] == STATUS_PENDING
        )
        running = self.queue.is_running()
        paused = self.queue.is_paused()

        if total == 0:
            self.queue_status_var.set("Queue empty.")
        else:
            bits = [f"{done}/{total} done"]
            if pending:
                bits.append(f"{pending} pending")
            if err:
                bits.append(f"{err} failed")
            if paused:
                bits.append("paused")
            elif running:
                bits.append("running")
            self.queue_status_var.set(" · ".join(bits))

        if running:
            self.queue_start_btn.config(state="disabled")
            self.queue_stop_btn.config(state="normal")
        else:
            self.queue_start_btn.config(state="normal")
            self.queue_stop_btn.config(state="disabled")

        self.queue_pause_btn.config(
            text="▶  Resume" if paused else "⏸  Pause"
        )

        if (
            total > 0
            and not running
            and done + err == total
            and getattr(self, "_last_queue_size", 0) != total
        ):
            self._last_queue_size = total
            self._notify(
                "Queue finished",
                f"{done} complete" + (f", {err} failed" if err else ""),
            )
        elif total == 0:
            self._last_queue_size = 0