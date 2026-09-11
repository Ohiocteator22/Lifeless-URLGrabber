import threading
import webbrowser
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import COLORS, resolution_label
from .. import downloader


class FormatsTabMixin:
    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def _build_formats_tab(self):
        tab = tk.Frame(self.notebook, bg=COLORS["surface"])
        self.notebook.add(tab, text="  FORMATS  ")

        inner = tk.Frame(tab, bg=COLORS["surface"])
        inner.pack(fill=BOTH, expand=True, padx=18, pady=18)

        tree_wrap = tk.Frame(inner, bg=COLORS["surface"])
        tree_wrap.pack(fill=BOTH, expand=True)

        cols = ("quality", "resolution", "fps", "format", "size", "id")
        self.tree = ttk.Treeview(
            tree_wrap,
            columns=cols,
            show="headings",
            style="Modern.Treeview",
            selectmode="browse",
        )
        headings = {
            "quality":    ("Quality",    110),
            "resolution": ("Resolution", 120),
            "fps":        ("FPS",         70),
            "format":     ("Container",  110),
            "size":       ("Size",       120),
            "id":         ("Format ID",  100),
        }
        for c, (text, width) in headings.items():
            self.tree.heading(c, text=text, anchor=W)
            self.tree.column(
                c,
                width=width,
                anchor=W,
                stretch=(c == "size"),
            )

        vsb = ttk.Scrollbar(
            tree_wrap,
            orient=VERTICAL,
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)
        self.tree.bind("<Double-1>", lambda e: self.download_selected())

        self._build_options_row(inner)
        self._build_format_context_menu()

    def _build_options_row(self, parent):
        opts = tk.Frame(
            parent,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        opts.pack(fill=X, pady=(14, 0))

        opts_inner = tk.Frame(opts, bg=COLORS["surface_2"])
        opts_inner.pack(fill=X, padx=14, pady=12)

        checks = tk.Frame(opts_inner, bg=COLORS["surface_2"])
        checks.pack(fill=X)

        self.opt_subs = tk.BooleanVar(value=False)
        self.opt_thumb = tk.BooleanVar(value=False)
        self.opt_trim = tk.BooleanVar(value=False)

        tk.Checkbutton(
            checks,
            text="Include subtitles (.srt)",
            variable=self.opt_subs,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0,
            command=self._on_subs_toggle,
        ).pack(side=LEFT, padx=(0, 20))

        tk.Checkbutton(
            checks,
            text="Download thumbnail (.jpg)",
            variable=self.opt_thumb,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0,
        ).pack(side=LEFT, padx=(0, 20))

        tk.Checkbutton(
            checks,
            text="Trim video",
            variable=self.opt_trim,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0,
            command=self._on_trim_toggle,
        ).pack(side=LEFT)

        self.subs_lang_var = tk.StringVar(value="en")
        self.subs_lang_entry = ttk.Entry(
            checks,
            textvariable=self.subs_lang_var,
            width=10,
            font=("Segoe UI", 10),
        )
        self.subs_lang_label = tk.Label(
            checks,
            text=" langs:",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 10),
        )

        self.trim_row = tk.Frame(opts_inner, bg=COLORS["surface_2"])

        self.trim_start_var = tk.StringVar(value="00:00:00")
        self.trim_end_var = tk.StringVar(value="")

        tk.Label(
            self.trim_row,
            text="Start:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)

        ttk.Entry(
            self.trim_row,
            textvariable=self.trim_start_var,
            width=12,
            font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(6, 14))

        tk.Label(
            self.trim_row,
            text="End:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)

        ttk.Entry(
            self.trim_row,
            textvariable=self.trim_end_var,
            width=12,
            font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(6, 14))

        tk.Label(
            self.trim_row,
            text="(HH:MM:SS — leave End empty to grab to the end)",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT)

    def _build_format_context_menu(self):
        self.format_menu = tk.Menu(
            self,
            tearoff=0,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            activebackground=COLORS["accent"],
            activeforeground="white",
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        self.format_menu.add_command(
            label="Copy Video URL",
            command=self._copy_video_url,
        )
        self.format_menu.add_command(
            label="Copy Format ID",
            command=self._copy_format_id,
        )
        self.format_menu.add_separator()
        self.format_menu.add_command(
            label="Open in Browser",
            command=self._open_in_browser,
        )
        self.tree.bind("<Button-3>", self._show_format_menu)

    # ------------------------------------------------------------------
    # Options toggles
    # ------------------------------------------------------------------
    def _on_subs_toggle(self):
        if self.opt_subs.get():
            self.subs_lang_label.pack(side=LEFT, padx=(6, 2))
            self.subs_lang_entry.pack(side=LEFT)
        else:
            self.subs_lang_label.pack_forget()
            self.subs_lang_entry.pack_forget()

    def _on_trim_toggle(self):
        if self.opt_trim.get():
            self.trim_row.pack(fill=X, pady=(10, 0))
        else:
            self.trim_row.pack_forget()

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------
    def _show_format_menu(self, event):
        row = self.tree.identify_row(event.y)
        if not row:
            return
        self.tree.selection_set(row)
        try:
            self.format_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.format_menu.grab_release()

    def _copy_video_url(self):
        url = self.url_var.get().strip()
        if not url:
            return
        self.clipboard_clear()
        self.clipboard_append(url)
        self._set_status("Copied video URL to clipboard.")

    def _copy_format_id(self):
        sel = self.tree.selection()
        if not sel:
            return
        fmt = self.format_map.get(sel[0])
        if not fmt:
            return
        self.clipboard_clear()
        self.clipboard_append(str(fmt.get("format_id", "")))
        self._set_status(f"Copied format ID: {fmt.get('format_id', '')}")

    def _open_in_browser(self):
        url = self.url_var.get().strip()
        if not url:
            return
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open browser:\n{e}")

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------
    def fetch_formats(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return

        self._clear_tree()
        self.notebook.select(0)
        self._set_status("Fetching formats…")

        threading.Thread(
            target=self._fetch_formats_thread,
            args=(url,),
            daemon=True,
        ).start()

    def _fetch_formats_thread(self, url):
        try:
            info = downloader.fetch_formats(url, self._cookie_opts())
        except Exception as e:
            self.after(0, lambda: self._show_fetch_error(str(e)))
            return

        self.video_info = info
        sorted_formats = downloader.filter_and_sort_formats(
            info.get("formats", [])
        )
        self.after(0, lambda: self._populate_tree(sorted_formats))

    def _populate_tree(self, formats):
        self._clear_tree()
        self.format_map.clear()

        if not formats:
            self._set_status("No video formats found.")
            return

        title = self.video_info.get("title", "Unknown title")
        self._set_status(f"Loaded: {title[:70]}")

        for i, f in enumerate(formats):
            height = f["height"]
            ext = (f.get("ext") or "???").upper()
            fps = f.get("fps")
            fps_str = f"{fps:.0f}" if fps else "—"
            size = f.get("filesize") or f.get("filesize_approx")
            size_str = f"{size / 1024 / 1024:.1f} MB" if size else "—"

            self.tree.insert(
                "",
                END,
                iid=str(i),
                values=(
                    resolution_label(height),
                    f"{height}p",
                    fps_str,
                    f".{ext.lower()}",
                    size_str,
                    f["format_id"],
                ),
            )
            self.format_map[str(i)] = f

    def _clear_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def _show_fetch_error(self, err):
        self._clear_tree()
        low = err.lower()
        if "login" in low or "sign in" in low or "cookie" in low:
            self._set_status("Login required — add cookies.txt")
            messagebox.showerror(
                "Login Required",
                "This site needs you to be logged in.\n\n"
                "Drop a cookies.txt file next to this app and try again.",
            )
        else:
            self._set_status(f"Error: {err[:80]}")
            messagebox.showerror("Error", err)

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------
    def download_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Error", "Please select a format first.")
            return

        fmt = self.format_map.get(sel[0])
        if not fmt:
            return

        url = self.url_var.get().strip()
        out_dir = self.output_path.get()
        height = fmt["height"]
        ext = (fmt.get("ext") or "mp4").lower()
        merge_ext = "mkv" if ext == "mkv" else "mp4"

        format_selector = downloader.build_format_selector(height)

        subs_on = self.opt_subs.get()
        subs_langs = self.subs_lang_var.get().strip() or "en"
        thumb_on = self.opt_thumb.get()

        trim_start = None
        trim_end = None
        if self.opt_trim.get():
            trim_start = downloader.parse_timecode(self.trim_start_var.get())
            trim_end = downloader.parse_timecode(self.trim_end_var.get())
            if (
                trim_start is None
                and trim_end is None
                and self.trim_start_var.get().strip() == ""
                and self.trim_end_var.get().strip() == ""
            ):
                messagebox.showwarning(
                    "Trim",
                    "Trim is enabled but both start and end are empty. "
                    "Fill at least one, or disable Trim.",
                )
                return

        title = "Unknown"
        if self.video_info:
            title = self.video_info.get("title", "Unknown")

        self._current_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "title": title,
            "url": url,
            "quality": resolution_label(height),
            "resolution": f"{height}p",
            "container": merge_ext,
            "format_id": fmt.get("format_id"),
            "output_dir": out_dir,
        }

        self.download_btn.config(state="disabled", text="⏳  Starting…")
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        self._set_status(f"Preparing {height}p {merge_ext.upper()}…")

        threading.Thread(
            target=self._download_thread,
            args=(
                url,
                format_selector,
                out_dir,
                merge_ext,
                subs_on,
                subs_langs,
                thumb_on,
                trim_start,
                trim_end,
            ),
            daemon=True,
        ).start()

    def _download_thread(
        self,
        url,
        format_selector,
        out_dir,
        merge_ext,
        subs_on,
        subs_langs,
        thumb_on,
        trim_start,
        trim_end,
    ):
        ydl_opts = downloader.build_ydl_opts(
            format_selector=format_selector,
            out_dir=out_dir,
            merge_ext=merge_ext,
            cookie_opts=self._cookie_opts(),
            progress_hook=self._progress_hook,
            subtitles=subs_on,
            subtitle_langs=subs_langs,
            thumbnail=thumb_on,
            trim_start=trim_start,
            trim_end=trim_end,
        )
        try:
            downloader.download(url, ydl_opts)
            self.after(0, lambda: self._download_done(True, None))
        except Exception as e:
            self.after(0, lambda: self._download_done(False, str(e)))

    # ------------------------------------------------------------------
    # Progress / completion
    # ------------------------------------------------------------------
    def _progress_hook(self, d):
        if d["status"] == "downloading":
            pct_str = d.get("_percent_str", "0%").strip().replace("%", "")
            try:
                pct = float(pct_str)
            except ValueError:
                pct = 0
            speed = d.get("_speed_str", "").strip()
            self.after(0, lambda: self._on_download_progress(pct, speed))
        elif d["status"] == "finished":
            self.after(
                0,
                lambda: self._update_progress(100, "Merging with FFmpeg…"),
            )

    def _on_download_progress(self, pct, speed):
        if str(self.progress["mode"]) == "indeterminate":
            self.progress.stop()
            self.progress.configure(mode="determinate")
            self.download_btn.config(text="⬇  Downloading…")
        self.progress["value"] = pct
        self._set_status(f"Downloading… {speed}")

    def _update_progress(self, pct, status):
        self.progress["value"] = pct
        self._set_status(status)

    def _download_done(self, success, err):
        try:
            self.progress.stop()
        except Exception:
            pass
        self.progress.configure(mode="determinate")
        self.download_btn.config(state="normal", text="⬇  Download")

        if success:
            self.progress["value"] = 100
            self._set_status("✅ Download complete")
            if self._current_record:
                self._add_to_history(self._current_record)
                self._current_record = None
            messagebox.showinfo("Success", "Download complete!")
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
                self._set_status("❌ Download failed")
                messagebox.showerror(
                    "Error",
                    f"Download failed:\n{err}",
                )