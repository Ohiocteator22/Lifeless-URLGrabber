import threading
import webbrowser
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import COLORS, resolution_label
from .. import downloader
from .. import profiles as profiles_mod
from .profiles_dialog import ProfilesDialog


class FormatsTabMixin:
    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def _build_formats_tab(self):
        tab = tk.Frame(self.notebook, bg=COLORS["surface"])
        self.notebook.add(tab, text="  FORMATS  ")

        inner = tk.Frame(tab, bg=COLORS["surface"])
        inner.pack(fill=BOTH, expand=True, padx=18, pady=18)

        self._build_profile_bar(inner)
        self._build_formats_tree(inner)
        self._build_options_row(inner)
        self._build_smart_pick_row(inner)
        self._build_format_context_menu()

    def _build_profile_bar(self, parent):
        bar = tk.Frame(
            parent,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        bar.pack(fill=X, pady=(0, 12))

        inner = tk.Frame(bar, bg=COLORS["surface_2"])
        inner.pack(fill=X, padx=14, pady=10)

        tk.Label(
            inner,
            text="Profile:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)

        self.profile_var = tk.StringVar(value="Custom")
        self.profile_combo = ttk.Combobox(
            inner,
            textvariable=self.profile_var,
            values=["Custom"],
            state="readonly",
            width=24,
            font=("Segoe UI", 10),
        )
        self.profile_combo.pack(side=LEFT, padx=(8, 8))
        self.profile_combo.bind(
            "<<ComboboxSelected>>", self._on_profile_changed
        )

        ttk.Button(
            inner,
            text="Manage Profiles",
            style="Ghost.TButton",
            command=self._open_profiles_dialog,
        ).pack(side=LEFT)

        self.profile_hint_var = tk.StringVar(value="")
        tk.Label(
            inner,
            textvariable=self.profile_hint_var,
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT, padx=14)

        self._refresh_profile_combo()

    def _build_formats_tree(self, parent):
        tree_wrap = tk.Frame(parent, bg=COLORS["surface"])
        tree_wrap.pack(fill=BOTH, expand=True)

        cols = (
            "quality",
            "resolution",
            "fps",
            "vcodec",
            "acodec",
            "hdr",
            "container",
            "size",
            "id",
        )
        self.tree = ttk.Treeview(
            tree_wrap,
            columns=cols,
            show="headings",
            style="Modern.Treeview",
            selectmode="browse",
        )
        headings = {
            "quality":    ("Quality",     75),
            "resolution": ("Resolution",  90),
            "fps":        ("FPS",         50),
            "vcodec":     ("Video",       65),
            "acodec":     ("Audio",       55),
            "hdr":        ("HDR",         65),
            "container":  ("Container",   75),
            "size":       ("Size",        90),
            "id":         ("Format ID",   85),
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

    def _build_options_row(self, parent):
        opts = tk.Frame(
            parent,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        opts.pack(fill=X, pady=(12, 0))

        inner = tk.Frame(opts, bg=COLORS["surface_2"])
        inner.pack(fill=X, padx=14, pady=12)

        checks = tk.Frame(inner, bg=COLORS["surface_2"])
        checks.pack(fill=X)

        self.opt_subs = tk.BooleanVar(value=False)
        self.opt_thumb = tk.BooleanVar(value=False)
        self.opt_trim = tk.BooleanVar(value=False)
        self.opt_sponsor = tk.BooleanVar(value=False)

        tk.Checkbutton(
            checks,
            text="Subtitles (.srt)",
            variable=self.opt_subs,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0,
            command=self._refresh_dynamic_row,
        ).pack(side=LEFT, padx=(0, 16))

        tk.Checkbutton(
            checks,
            text="Thumbnail (.jpg)",
            variable=self.opt_thumb,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0,
        ).pack(side=LEFT, padx=(0, 16))

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
            command=self._refresh_dynamic_row,
        ).pack(side=LEFT, padx=(0, 16))

        tk.Checkbutton(
            checks,
            text="Skip sponsor segments",
            variable=self.opt_sponsor,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0,
            command=self._refresh_dynamic_row,
        ).pack(side=LEFT)

        self.dynamic_row = tk.Frame(inner, bg=COLORS["surface_2"])

        self.subs_group = tk.Frame(self.dynamic_row, bg=COLORS["surface_2"])
        tk.Label(
            self.subs_group,
            text="Langs:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)
        self.subs_lang_var = tk.StringVar(value="en")
        ttk.Entry(
            self.subs_group,
            textvariable=self.subs_lang_var,
            width=14,
            font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(6, 0))

        self.sponsor_group = tk.Frame(
            self.dynamic_row, bg=COLORS["surface_2"]
        )
        tk.Label(
            self.sponsor_group,
            text="Categories:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)
        self.sponsor_cats_var = tk.StringVar(value="sponsor,selfpromo")
        ttk.Entry(
            self.sponsor_group,
            textvariable=self.sponsor_cats_var,
            width=28,
            font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(6, 0))

        self.trim_group = tk.Frame(self.dynamic_row, bg=COLORS["surface_2"])
        tk.Label(
            self.trim_group,
            text="Start:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)
        self.trim_start_var = tk.StringVar(value="00:00:00")
        ttk.Entry(
            self.trim_group,
            textvariable=self.trim_start_var,
            width=11,
            font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(6, 12))
        tk.Label(
            self.trim_group,
            text="End:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)
        self.trim_end_var = tk.StringVar(value="")
        ttk.Entry(
            self.trim_group,
            textvariable=self.trim_end_var,
            width=11,
            font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(6, 12))
        tk.Label(
            self.trim_group,
            text="(empty End = to the end)",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT)

        args_row = tk.Frame(inner, bg=COLORS["surface_2"])
        args_row.pack(fill=X, pady=(12, 0))

        tk.Label(
            args_row,
            text="Custom yt-dlp args:",
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)

        self.custom_args_var = tk.StringVar(value="")
        ttk.Entry(
            args_row,
            textvariable=self.custom_args_var,
            font=("Consolas", 10),
        ).pack(side=LEFT, fill=X, expand=True, padx=(10, 0))

        tk.Label(
            args_row,
            text="  e.g. --proxy socks5://127.0.0.1:1080",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=LEFT)

    def _build_smart_pick_row(self, parent):
        row = tk.Frame(
            parent,
            bg=COLORS["surface_2"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        row.pack(fill=X, pady=(12, 0))

        inner = tk.Frame(row, bg=COLORS["surface_2"])
        inner.pack(fill=X, padx=14, pady=12)

        ttk.Button(
            inner,
            text="🤖  Smart Pick",
            style="Accent.TButton",
            command=self._smart_pick,
        ).pack(side=LEFT)

        self.inline_download_btn = ttk.Button(
            inner,
            text="⬇  Download",
            style="Success.TButton",
            command=self.download_selected,
        )
        self.inline_download_btn.pack(side=LEFT, padx=(10, 0))

        self.smart_info_var = tk.StringVar(value="No format picked yet.")
        tk.Label(
            inner,
            textvariable=self.smart_info_var,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Consolas", 9),
            justify=LEFT,
        ).pack(side=LEFT, padx=14, anchor=W)

    def _set_download_buttons(self, state, text):
        for attr in ("download_btn", "inline_download_btn"):
            btn = getattr(self, attr, None)
            if btn is None:
                continue
            try:
                btn.config(state=state, text=text)
            except Exception:
                pass

    def _refresh_dynamic_row(self):
        self.subs_group.pack_forget()
        self.sponsor_group.pack_forget()
        self.trim_group.pack_forget()

        any_visible = False
        if self.opt_subs.get():
            self.subs_group.pack(side=LEFT, padx=(0, 20))
            any_visible = True
        if self.opt_sponsor.get():
            self.sponsor_group.pack(side=LEFT, padx=(0, 20))
            any_visible = True
        if self.opt_trim.get():
            self.trim_group.pack(side=LEFT)
            any_visible = True

        if any_visible:
            self.dynamic_row.pack(fill=X, pady=(10, 0))
        else:
            self.dynamic_row.pack_forget()

    # ------------------------------------------------------------------
    # Profiles
    # ------------------------------------------------------------------
    def _refresh_profile_combo(self):
        names = ["Custom"] + [
            p.get("name", "Unnamed") for p in self.profiles
        ]
        self.profile_combo.config(values=names)
        if self.profile_var.get() not in names:
            self.profile_var.set("Custom")

    def _active_profile(self):
        name = self.profile_var.get()
        if name == "Custom":
            return None
        return profiles_mod.get_profile_by_name(self.profiles, name)

    def _on_profile_changed(self, event=None):
        profile = self._active_profile()
        if not profile:
            self.profile_hint_var.set("")
            return

        self.opt_subs.set(bool(profile.get("subtitles", False)))
        self.opt_thumb.set(bool(profile.get("thumbnail", False)))
        self.opt_sponsor.set(bool(profile.get("sponsorblock", False)))
        self._refresh_dynamic_row()

        bits = []
        if profile.get("audio_only"):
            bits.append(f"MP3 {profile.get('audio_bitrate')}kbps")
        else:
            h = profile.get("max_height") or 0
            if h:
                bits.append(f"{h}p")
            bits.append(profile.get("container", "mp4"))
        folder = profile.get("output_folder") or "(main folder)"
        bits.append(f"→ {folder}")
        self.profile_hint_var.set("  ·  ".join(bits))

    def _open_profiles_dialog(self):
        ProfilesDialog(self, self.profiles, self._on_profiles_saved)

    def _on_profiles_saved(self, new_profiles):
        self.profiles = new_profiles
        profiles_mod.save_profiles(self.profiles)
        self._refresh_profile_combo()

    # ------------------------------------------------------------------
    # Smart pick
    # ------------------------------------------------------------------
    def _smart_pick(self):
        if not self.format_map:
            messagebox.showinfo(
                "Smart Pick",
                "Fetch formats first — paste a URL and click Fetch.",
            )
            return

        profile = self._active_profile()
        if not profile:
            profile = {
                "max_height": 1080,
                "min_fps": 0,
                "container": "mp4",
                "video_codec_pref": "any",
                "audio_codec_pref": "any",
                "prefer_hdr": False,
            }

        formats = list(self.format_map.values())
        pick = downloader.pick_smart_format(formats, profile)
        if not pick:
            self.smart_info_var.set("No suitable format found.")
            return

        fid = pick.get("format_id")
        target_iid = None
        for iid, f in self.format_map.items():
            if f.get("format_id") == fid:
                target_iid = iid
                break

        if target_iid is not None:
            self.tree.selection_set(target_iid)
            self.tree.focus(target_iid)
            self.tree.see(target_iid)

        summary = downloader.describe_pick(pick, profile)
        self.smart_info_var.set(summary.replace("\n", "   "))

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------
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
            ext = (f.get("ext") or "???").lower()
            fps = f.get("fps")
            fps_str = f"{fps:.0f}" if fps else "—"
            size = downloader.estimate_size(f)
            size_str = f"{size / 1024 / 1024:.1f} MB" if size else "—"

            self.tree.insert(
                "",
                END,
                iid=str(i),
                values=(
                    resolution_label(height),
                    f"{height}p",
                    fps_str,
                    downloader.shorten_vcodec(f.get("vcodec")),
                    downloader.shorten_acodec(f.get("acodec")),
                    downloader.hdr_label(f),
                    f".{ext}",
                    size_str,
                    f["format_id"],
                ),
            )
            self.format_map[str(i)] = f

        if self._active_profile():
            self.after(50, self._smart_pick)

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

        profile = self._active_profile()
        url = self.url_var.get().strip()

        base_out = self.output_path.get()
        out_dir = base_out
        if profile:
            out_dir = profiles_mod.resolve_output_dir(profile, base_out)

        height = fmt["height"]
        ext = (fmt.get("ext") or "mp4").lower()
        merge_ext = "mkv" if ext == "mkv" else "mp4"
        if profile and profile.get("container"):
            merge_ext = profile["container"]

        format_selector = downloader.build_format_selector(height)

        subs_on = self.opt_subs.get()
        subs_langs = self.subs_lang_var.get().strip() or "en"
        thumb_on = self.opt_thumb.get()
        sponsor_on = self.opt_sponsor.get()
        sponsor_cats = self.sponsor_cats_var.get().strip() or "sponsor"
        custom_args = self.custom_args_var.get().strip()

        if custom_args:
            _, err = downloader.parse_custom_args(custom_args)
            if err:
                messagebox.showerror(
                    "Invalid custom args",
                    f"Could not parse your custom yt-dlp args:\n\n{err}",
                )
                return

        trim_start = None
        trim_end = None
        if self.opt_trim.get():
            trim_start = downloader.parse_timecode(
                self.trim_start_var.get()
            )
            trim_end = downloader.parse_timecode(self.trim_end_var.get())
            if (
                trim_start is None
                and trim_end is None
                and self.trim_start_var.get().strip() == ""
                and self.trim_end_var.get().strip() == ""
            ):
                messagebox.showwarning(
                    "Trim",
                    "Trim is enabled but both start and end are empty.",
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

        self._set_download_buttons("disabled", "⏳  Starting…")
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        self._set_status(f"Preparing {height}p {merge_ext.upper()}…")

        threading.Thread(
            target=self._download_thread,
            args=(url, format_selector, out_dir, merge_ext),
            kwargs={
                "subs_on": subs_on,
                "subs_langs": subs_langs,
                "thumb_on": thumb_on,
                "trim_start": trim_start,
                "trim_end": trim_end,
                "sponsor_on": sponsor_on,
                "sponsor_cats": sponsor_cats,
                "custom_args": custom_args,
            },
            daemon=True,
        ).start()

    def _download_thread(
        self,
        url,
        format_selector,
        out_dir,
        merge_ext,
        subs_on=False,
        subs_langs="en",
        thumb_on=False,
        trim_start=None,
        trim_end=None,
        sponsor_on=False,
        sponsor_cats="sponsor",
        custom_args="",
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
            sponsorblock=sponsor_on,
            sponsorblock_categories=sponsor_cats,
            custom_args=custom_args,
            net_opts=self._net_opts(),
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
            self._set_download_buttons("disabled", "⬇  Downloading…")
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
        self._set_download_buttons("normal", "⬇  Download")

        if success:
            self.progress["value"] = 100
            self._set_status("✅ Download complete")
            if self._current_record:
                self._add_to_history(self._current_record)
                self._current_record = None
            self._notify("Download complete", "Your video is ready.")
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