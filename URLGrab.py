import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import yt_dlp


# ======================================================================
# FROZEN-AWARE PATHS
# ======================================================================
def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)


def user_path(relative):
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)


BASE_DIR = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)

FFMPEG_DIR = resource_path("") if getattr(sys, "frozen", False) else BASE_DIR

ARIA2C_PATH = resource_path("aria2c.exe")
if not os.path.isfile(ARIA2C_PATH):
    alt = os.path.join(BASE_DIR, "aria2c.exe")
    ARIA2C_PATH = alt if os.path.isfile(alt) else None

COOKIES_FILE = user_path("cookies.txt")


COLORS = {
    "bg":          "#0d0f14",
    "surface":     "#151821",
    "surface_2":   "#1b1f2b",
    "border":      "#232838",
    "text":        "#e7e9f0",
    "text_dim":    "#7f869c",
    "accent":      "#7c5cff",
    "accent_hov":  "#8f74ff",
    "success":     "#10b981",
    "success_hov": "#14c98f",
}


class URLGrabApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("URLGrab")
        self.geometry("940x700")
        self.minsize(780, 580)
        self.configure(bg=COLORS["bg"])

        self.video_info = None
        self.format_map = {}
        self.url_var = tk.StringVar()
        self.output_path = tk.StringVar(value=BASE_DIR)
        self.status_var = tk.StringVar(value="Ready")

        self._build_styles()
        self._build_ui()
        self._notify_cookies_status()

    # ==================================================================
    # STYLES
    # ==================================================================
    def _build_styles(self):
        style = ttk.Style()

        style.configure(
            "Modern.Treeview",
            background=COLORS["surface"],
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            borderwidth=0,
            relief="flat",
            rowheight=38,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=COLORS["surface_2"],
            foreground=COLORS["text_dim"],
            borderwidth=0,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 10),
        )
        style.map(
            "Modern.Treeview",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", "white")],
        )
        style.map(
            "Modern.Treeview.Heading",
            background=[("active", COLORS["surface_2"])],
        )

        style.configure(
            "Modern.TEntry",
            fieldbackground=COLORS["surface_2"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            insertcolor=COLORS["text"],
            padding=12,
            relief="flat",
        )
        style.map(
            "Modern.TEntry",
            bordercolor=[("focus", COLORS["accent"])],
            lightcolor=[("focus", COLORS["accent"])],
            darkcolor=[("focus", COLORS["accent"])],
        )

        style.configure(
            "Accent.TButton",
            background=COLORS["accent"],
            foreground="white",
            borderwidth=0,
            focuscolor=COLORS["accent"],
            padding=(22, 12),
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map(
            "Accent.TButton",
            background=[
                ("active", COLORS["accent_hov"]),
                ("pressed", COLORS["accent"]),
            ],
        )

        style.configure(
            "Success.TButton",
            background=COLORS["success"],
            foreground="white",
            borderwidth=0,
            focuscolor=COLORS["success"],
            padding=(22, 12),
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map(
            "Success.TButton",
            background=[
                ("active", COLORS["success_hov"]),
                ("pressed", COLORS["success"]),
            ],
        )

        style.configure(
            "Ghost.TButton",
            background=COLORS["surface_2"],
            foreground=COLORS["text"],
            borderwidth=0,
            focuscolor=COLORS["surface_2"],
            padding=(16, 10),
            font=("Segoe UI", 10),
            relief="flat",
        )
        style.map(
            "Ghost.TButton",
            background=[
                ("active", COLORS["border"]),
                ("pressed", COLORS["surface_2"]),
            ],
        )

        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor=COLORS["surface_2"],
            background=COLORS["accent"],
            bordercolor=COLORS["surface_2"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["accent"],
            thickness=6,
        )

    # ==================================================================
    # UI
    # ==================================================================
    def _build_ui(self):
        root = tk.Frame(self, bg=COLORS["bg"])
        root.pack(fill=BOTH, expand=True, padx=26, pady=22)

        # ---------- HEADER ----------
        header = tk.Frame(root, bg=COLORS["bg"])
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

        # ---------- URL CARD ----------
        url_card = tk.Frame(
            root,
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

        ttk.Button(
            url_row,
            text="Fetch",
            style="Accent.TButton",
            command=self.fetch_formats,
        ).pack(side=LEFT)

        # ---------- FORMATS CARD ----------
        fmt_card = tk.Frame(
            root,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        fmt_card.pack(fill=BOTH, expand=True, pady=(0, 14))

        fmt_inner = tk.Frame(fmt_card, bg=COLORS["surface"])
        fmt_inner.pack(fill=BOTH, expand=True, padx=18, pady=18)

        tk.Label(
            fmt_inner,
            text="AVAILABLE FORMATS",
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, pady=(0, 10))

        tree_wrap = tk.Frame(fmt_inner, bg=COLORS["surface"])
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

        # ---------- FOOTER CARD ----------
        footer = tk.Frame(
            root,
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

    # ==================================================================
    # COOKIES
    # ==================================================================
    def _notify_cookies_status(self):
        if os.path.isfile(COOKIES_FILE):
            self._set_status("cookies.txt detected — Instagram/FB enabled.")

    def _cookie_opts(self):
        if os.path.isfile(COOKIES_FILE):
            return {"cookiefile": COOKIES_FILE}
        return {}

    # ==================================================================
    # FETCH FORMATS
    # ==================================================================
    def fetch_formats(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return

        self._clear_tree()
        self._set_status("Fetching formats…")

        threading.Thread(
            target=self._fetch_formats_thread,
            args=(url,),
            daemon=True,
        ).start()

    def _fetch_formats_thread(self, url):
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            **self._cookie_opts(),
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            self.after(0, lambda: self._show_fetch_error(str(e)))
            return

        self.video_info = info
        formats = info.get("formats", [])

        best_by_key = {}
        for f in formats:
            if f.get("vcodec") in (None, "none"):
                continue
            height = f.get("height")
            if not height:
                continue
            ext = f.get("ext", "mp4")
            key = (height, ext)
            prev = best_by_key.get(key)
            if prev is None or (f.get("tbr") or 0) > (prev.get("tbr") or 0):
                best_by_key[key] = f

        sorted_formats = sorted(
            best_by_key.values(),
            key=lambda x: (x["height"], x.get("tbr") or 0),
            reverse=True,
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

            quality = self._resolution_label(height)

            self.tree.insert(
                "",
                END,
                iid=str(i),
                values=(
                    quality,
                    f"{height}p",
                    fps_str,
                    f".{ext.lower()}",
                    size_str,
                    f["format_id"],
                ),
            )
            self.format_map[str(i)] = f

    @staticmethod
    def _resolution_label(height):
        if height >= 2160:
            return "4K"
        if height >= 1440:
            return "2K"
        if height >= 1080:
            return "FHD"
        if height >= 720:
            return "HD"
        if height >= 480:
            return "SD"
        return "LOW"

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

    def _set_status(self, text):
        self.status_var.set(text)

    # ==================================================================
    # DOWNLOAD
    # ==================================================================
    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_path.get())
        if folder:
            self.output_path.set(folder)

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

        format_selector = (
            f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
        )

        # ---- Immediate feedback so users know it's working ----
        self.download_btn.config(state="disabled", text="⏳  Starting…")
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        self._set_status(f"Preparing {height}p {merge_ext.upper()}…")

        threading.Thread(
            target=self._download_thread,
            args=(url, format_selector, out_dir, merge_ext),
            daemon=True,
        ).start()

    def _download_thread(self, url, format_selector, out_dir, merge_ext):
        ydl_opts = {
            "format": format_selector,
            "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
            "merge_output_format": merge_ext,
            "ffmpeg_location": FFMPEG_DIR,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "progress_hooks": [self._progress_hook],
            "concurrent_fragment_downloads": 10,
            "http_chunk_size": 10485760,
            "retries": 10,
            "fragment_retries": 10,
            "buffersize": 1024 * 1024,
            **self._cookie_opts(),
        }

        if ARIA2C_PATH:
            ydl_opts.update(
                {
                    "external_downloader": ARIA2C_PATH,
                    "external_downloader_args": {
                        "aria2c": [
                            "-x", "16",
                            "-s", "16",
                            "-k", "1M",
                            "--min-split-size=1M",
                            "--max-connection-per-server=16",
                            "--file-allocation=none",
                            "--console-log-level=warn",
                            "--summary-interval=0",
                        ]
                    },
                }
            )

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, lambda: self._download_done(True, None))
        except Exception as e:
            self.after(0, lambda: self._download_done(False, str(e)))

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
        # First real progress → flip from indeterminate to determinate
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


if __name__ == "__main__":
    app = URLGrabApp()
    app.mainloop()