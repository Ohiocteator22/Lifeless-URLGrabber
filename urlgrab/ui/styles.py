import ttkbootstrap as ttk

from ..config import COLORS


def build_styles():
    style = ttk.Style()

    style.configure(
        "Modern.Treeview",
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
        borderwidth=0,
        relief="flat",
        rowheight=36,
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

    style.configure(
        "Modern.TNotebook",
        background=COLORS["bg"],
        borderwidth=0,
        tabmargins=(0, 0, 0, 0),
    )
    style.configure(
        "Modern.TNotebook.Tab",
        background=COLORS["surface"],
        foreground=COLORS["text_dim"],
        padding=(20, 10),
        font=("Segoe UI", 10, "bold"),
        borderwidth=0,
    )
    style.map(
        "Modern.TNotebook.Tab",
        background=[("selected", COLORS["surface_2"])],
        foreground=[("selected", COLORS["text"])],
    )