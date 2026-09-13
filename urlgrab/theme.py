from . import config


THEMES = {
    "Dark": {
        "ttk": "darkly",
        "bg":         "#0d0f14",
        "surface":    "#151821",
        "surface_2":  "#1b1f2b",
        "border":     "#232838",
        "text":       "#e7e9f0",
        "text_dim":   "#7f869c",
        "accent":     "#7c5cff",
        "accent_hov": "#8f74ff",
        "success":    "#10b981",
        "success_hov":"#14c98f",
        "danger":     "#ef4444",
        "danger_hov": "#f56565",
    },
    "Light": {
        "ttk": "flatly",
        "bg":         "#f4f6fa",
        "surface":    "#ffffff",
        "surface_2":  "#eef1f7",
        "border":     "#d8dee8",
        "text":       "#1a1f2b",
        "text_dim":   "#6b7280",
        "accent":     "#6d4aff",
        "accent_hov": "#5837e8",
        "success":    "#059669",
        "success_hov":"#047857",
        "danger":     "#dc2626",
        "danger_hov": "#b91c1c",
    },
    "Cyberpunk": {
        "ttk": "cyborg",
        "bg":         "#050510",
        "surface":    "#0d0a1f",
        "surface_2":  "#151030",
        "border":     "#2d1b5e",
        "text":       "#e0d7ff",
        "text_dim":   "#8b7fc7",
        "accent":     "#ff2bb1",
        "accent_hov": "#ff5cc4",
        "success":    "#00e5a0",
        "success_hov":"#00c78a",
        "danger":     "#ff3355",
        "danger_hov": "#cc2044",
    },
    "Solarized": {
        "ttk": "solar",
        "bg":         "#002b36",
        "surface":    "#073642",
        "surface_2":  "#0a4551",
        "border":     "#13545f",
        "text":       "#eee8d5",
        "text_dim":   "#93a1a1",
        "accent":     "#268bd2",
        "accent_hov": "#1e6fa8",
        "success":    "#859900",
        "success_hov":"#6d7d00",
        "danger":     "#dc322f",
        "danger_hov": "#b02724",
    },
}


def apply_theme(name):
    """Mutate config.COLORS in place and return the ttkbootstrap theme name."""
    preset = THEMES.get(name) or THEMES["Dark"]
    for key, value in preset.items():
        if key == "ttk":
            continue
        config.COLORS[key] = value
    return preset["ttk"]