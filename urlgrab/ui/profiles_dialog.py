import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..config import COLORS


CODEC_OPTIONS = ["any", "h264", "h265", "av1", "vp9"]
CONTAINER_OPTIONS = ["mp4", "mkv", "webm"]
FPS_OPTIONS = ["0", "24", "30", "60", "120"]
HEIGHT_OPTIONS = ["0", "480", "720", "1080", "1440", "2160"]
BITRATE_OPTIONS = ["128", "192", "256", "320"]


class ProfilesDialog(tk.Toplevel):
    def __init__(self, master, profiles, on_save):
        super().__init__(master)
        self.on_save = on_save
        self.profiles = [dict(p) for p in profiles]
        self.current_index = 0

        self.title("Manage Profiles")
        self.configure(bg=COLORS["bg"])
        self.geometry("640x600")
        self.transient(master)
        self.grab_set()

        self._build()
        self._load_profile(0)
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _build(self):
        root = tk.Frame(self, bg=COLORS["bg"])
        root.pack(fill=BOTH, expand=True, padx=20, pady=20)

        tk.Label(
            root,
            text="Download Profiles",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor=W)

        tk.Label(
            root,
            text="Save presets for common download scenarios.",
            bg=COLORS["bg"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 10),
        ).pack(anchor=W, pady=(2, 14))

        # List + form side by side
        body = tk.Frame(root, bg=COLORS["bg"])
        body.pack(fill=BOTH, expand=True)

        left = tk.Frame(body, bg=COLORS["surface_2"])
        left.pack(side=LEFT, fill=Y, padx=(0, 12))

        tk.Label(
            left,
            text="PROFILES",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=W, padx=10, pady=(10, 6))

        list_wrap = tk.Frame(left, bg=COLORS["surface_2"])
        list_wrap.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))

        self.listbox = tk.Listbox(
            list_wrap,
            width=22,
            height=16,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="white",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
            activestyle="none",
            highlightthickness=0,
        )
        self.listbox.pack(fill=BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_list_select)

        btn_col = tk.Frame(left, bg=COLORS["surface_2"])
        btn_col.pack(fill=X, padx=10, pady=(0, 10))

        ttk.Button(
            btn_col,
            text="+ New",
            style="Ghost.TButton",
            command=self._new_profile,
        ).pack(fill=X, pady=(0, 4))

        ttk.Button(
            btn_col,
            text="🗑 Delete",
            style="Ghost.TButton",
            command=self._delete_profile,
        ).pack(fill=X)

        right = tk.Frame(body, bg=COLORS["surface_2"])
        right.pack(side=LEFT, fill=BOTH, expand=True)

        form = tk.Frame(right, bg=COLORS["surface_2"])
        form.pack(fill=BOTH, expand=True, padx=14, pady=14)

        self.name_var = tk.StringVar()
        self._add_entry(form, "Name", self.name_var)

        self.max_height_var = tk.StringVar()
        self._add_combo(
            form, "Max height", self.max_height_var, HEIGHT_OPTIONS
        )

        self.min_fps_var = tk.StringVar()
        self._add_combo(
            form, "Min FPS", self.min_fps_var, FPS_OPTIONS
        )

        self.container_var = tk.StringVar()
        self._add_combo(
            form, "Container", self.container_var, CONTAINER_OPTIONS
        )

        self.vcodec_var = tk.StringVar()
        self._add_combo(
            form, "Video codec", self.vcodec_var, CODEC_OPTIONS
        )

        self.acodec_var = tk.StringVar()
        self._add_combo(
            form, "Audio codec", self.acodec_var, CODEC_OPTIONS
        )

        self.audio_only_var = tk.BooleanVar()
        self.audio_bitrate_var = tk.StringVar()

        audio_row = tk.Frame(form, bg=COLORS["surface_2"])
        audio_row.pack(fill=X, pady=(8, 0))

        tk.Checkbutton(
            audio_row,
            text="Audio only (MP3)",
            variable=self.audio_only_var,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            activebackground=COLORS["surface_2"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["surface"],
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0,
        ).pack(side=LEFT)

        ttk.Combobox(
            audio_row,
            textvariable=self.audio_bitrate_var,
            values=BITRATE_OPTIONS,
            state="readonly",
            width=6,
            font=("Segoe UI", 10),
        ).pack(side=LEFT, padx=(10, 4))

        tk.Label(
            audio_row,
            text="kbps",
            bg=COLORS["surface_2"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 10),
        ).pack(side=LEFT)

        self.output_var = tk.StringVar()
        self._add_entry(
            form,
            "Output folder",
            self.output_var,
            hint="empty = use main folder, or a subfolder name",
        )

        toggles = tk.Frame(form, bg=COLORS["surface_2"])
        toggles.pack(fill=X, pady=(12, 0))

        self.subs_var = tk.BooleanVar()
        self.thumb_var = tk.BooleanVar()
        self.sponsor_var = tk.BooleanVar()
        self.hdr_var = tk.BooleanVar()

        for label, var in [
            ("Subtitles", self.subs_var),
            ("Thumbnail", self.thumb_var),
            ("Skip sponsors", self.sponsor_var),
            ("Prefer HDR", self.hdr_var),
        ]:
            tk.Checkbutton(
                toggles,
                text=label,
                variable=var,
                bg=COLORS["surface_2"],
                fg=COLORS["text"],
                activebackground=COLORS["surface_2"],
                activeforeground=COLORS["text"],
                selectcolor=COLORS["surface"],
                font=("Segoe UI", 10),
                borderwidth=0,
                highlightthickness=0,
            ).pack(anchor=W)

        # Footer
        footer = tk.Frame(root, bg=COLORS["bg"])
        footer.pack(fill=X, pady=(14, 0))

        ttk.Button(
            footer,
            text="Cancel",
            style="Ghost.TButton",
            command=self._cancel,
        ).pack(side=RIGHT, padx=(8, 0))

        ttk.Button(
            footer,
            text="Save",
            style="Success.TButton",
            command=self._save,
        ).pack(side=RIGHT)

        self._refresh_list()

    def _add_entry(self, parent, label, var, hint=None):
        row = tk.Frame(parent, bg=COLORS["surface_2"])
        row.pack(fill=X, pady=(0, 8))

        tk.Label(
            row,
            text=label,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
            width=14,
            anchor=W,
        ).pack(side=LEFT)

        ttk.Entry(row, textvariable=var, font=("Segoe UI", 10)).pack(
            side=LEFT, fill=X, expand=True
        )

        if hint:
            tk.Label(
                row,
                text=hint,
                bg=COLORS["surface_2"],
                fg=COLORS["text_dim"],
                font=("Segoe UI", 8),
            ).pack(side=LEFT, padx=(6, 0))

    def _add_combo(self, parent, label, var, values):
        row = tk.Frame(parent, bg=COLORS["surface_2"])
        row.pack(fill=X, pady=(0, 8))

        tk.Label(
            row,
            text=label,
            bg=COLORS["surface_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
            width=14,
            anchor=W,
        ).pack(side=LEFT)

        ttk.Combobox(
            row,
            textvariable=var,
            values=values,
            state="readonly",
            width=10,
            font=("Segoe UI", 10),
        ).pack(side=LEFT)

    # ------------------------------------------------------------------
    # List handling
    # ------------------------------------------------------------------
    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for p in self.profiles:
            self.listbox.insert(tk.END, p.get("name", "Unnamed"))
        if self.profiles:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_index)

    def _on_list_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._save_current()
        self.current_index = sel[0]
        self._load_profile(self.current_index)

    def _load_profile(self, idx):
        if not self.profiles or idx >= len(self.profiles):
            return
        p = self.profiles[idx]
        self.name_var.set(p.get("name", ""))
        self.max_height_var.set(str(p.get("max_height", 1080)))
        self.min_fps_var.set(str(p.get("min_fps", 0)))
        self.container_var.set(p.get("container", "mp4"))
        self.vcodec_var.set(p.get("video_codec_pref", "any"))
        self.acodec_var.set(p.get("audio_codec_pref", "any"))
        self.audio_only_var.set(bool(p.get("audio_only", False)))
        self.audio_bitrate_var.set(str(p.get("audio_bitrate", "192")))
        self.output_var.set(p.get("output_folder", ""))
        self.subs_var.set(bool(p.get("subtitles", False)))
        self.thumb_var.set(bool(p.get("thumbnail", False)))
        self.sponsor_var.set(bool(p.get("sponsorblock", False)))
        self.hdr_var.set(bool(p.get("prefer_hdr", False)))

    def _save_current(self):
        if not self.profiles or self.current_index >= len(self.profiles):
            return

        def _int(val, default=0):
            try:
                return int(val)
            except (TypeError, ValueError):
                return default

        self.profiles[self.current_index] = {
            "name": self.name_var.get().strip() or "Unnamed",
            "max_height": _int(self.max_height_var.get(), 1080),
            "min_fps": _int(self.min_fps_var.get(), 0),
            "container": self.container_var.get() or "mp4",
            "video_codec_pref": self.vcodec_var.get() or "any",
            "audio_codec_pref": self.acodec_var.get() or "any",
            "audio_only": bool(self.audio_only_var.get()),
            "audio_bitrate": self.audio_bitrate_var.get() or "192",
            "output_folder": self.output_var.get().strip(),
            "subtitles": bool(self.subs_var.get()),
            "thumbnail": bool(self.thumb_var.get()),
            "sponsorblock": bool(self.sponsor_var.get()),
            "prefer_hdr": bool(self.hdr_var.get()),
        }

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def _new_profile(self):
        self._save_current()
        self.profiles.append(
            {
                "name": "New Profile",
                "max_height": 1080,
                "min_fps": 0,
                "container": "mp4",
                "video_codec_pref": "any",
                "audio_codec_pref": "any",
                "audio_only": False,
                "audio_bitrate": "192",
                "output_folder": "",
                "subtitles": False,
                "thumbnail": False,
                "sponsorblock": False,
                "prefer_hdr": False,
            }
        )
        self.current_index = len(self.profiles) - 1
        self._refresh_list()
        self._load_profile(self.current_index)

    def _delete_profile(self):
        if len(self.profiles) <= 1:
            messagebox.showinfo(
                "Cannot delete",
                "You need at least one profile.",
            )
            return
        if not messagebox.askyesno(
            "Delete profile",
            f"Delete '{self.profiles[self.current_index].get('name')}'?",
        ):
            return
        del self.profiles[self.current_index]
        self.current_index = max(0, self.current_index - 1)
        self._refresh_list()
        self._load_profile(self.current_index)

    def _save(self):
        self._save_current()
        self.on_save(self.profiles)
        self.destroy()

    def _cancel(self):
        self.destroy()