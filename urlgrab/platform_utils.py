import os
import platform
import subprocess
import sys


def is_windows():
    return sys.platform.startswith("win")


def is_macos():
    return sys.platform == "darwin"


def is_linux():
    return sys.platform.startswith("linux")


def binary_ext():
    return ".exe" if is_windows() else ""


def find_binary(name, search_dirs):
    if name.lower().endswith(".exe"):
        base = name[:-4]
    else:
        base = name

    ext = binary_ext()
    target = base + ext

    for d in search_dirs:
        if not d:
            continue
        candidate = os.path.join(d, target)
        if os.path.isfile(candidate):
            return candidate

    from shutil import which
    found = which(base)
    if found:
        return found
    return None


def open_in_file_manager(path):
    if not path or not os.path.exists(path):
        return False
    try:
        if is_windows():
            os.startfile(path)
        elif is_macos():
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False


def open_url(url):
    import webbrowser
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def get_wifi_status():
    try:
        if is_windows():
            return _wifi_windows()
        if is_macos():
            return _wifi_macos()
        if is_linux():
            return _wifi_linux()
    except Exception:
        return None
    return None


def _wifi_windows():
    flags = 0
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        flags = subprocess.CREATE_NO_WINDOW
    proc = subprocess.run(
        ["netsh", "interface", "show", "interface"],
        capture_output=True,
        text=True,
        timeout=4,
        creationflags=flags,
    )
    for line in proc.stdout.splitlines():
        low = line.lower()
        if "wi-fi" in low or "wireless" in low:
            if "connected" in low:
                return True
    return False


def _wifi_macos():
    try:
        proc = subprocess.run(
            ["networksetup", "-getairportnetwork", "en0"],
            capture_output=True,
            text=True,
            timeout=4,
        )
        out = proc.stdout.lower()
        if "current wi-fi network" in out:
            return True
        return False
    except Exception:
        pass

    try:
        proc = subprocess.run(
            ["networksetup", "-listallhardwareports"],
            capture_output=True,
            text=True,
            timeout=4,
        )
        return "wi-fi" in proc.stdout.lower()
    except Exception:
        return None


def _wifi_linux():
    try:
        proc = subprocess.run(
            ["nmcli", "-t", "-f", "TYPE,STATE", "dev", "status"],
            capture_output=True,
            text=True,
            timeout=4,
        )
        for line in proc.stdout.splitlines():
            if line.startswith("wifi:") and "connected" in line.lower():
                return True
        return False
    except Exception:
        return None


def get_app_icon_paths(icon_name="icon"):
    exts = []
    if is_windows():
        exts = [".ico", ".png"]
    elif is_macos():
        exts = [".icns", ".png"]
    else:
        exts = [".png", ".ico"]

    paths = []
    if hasattr(sys, "_MEIPASS"):
        for ext in exts:
            paths.append(os.path.join(sys._MEIPASS, icon_name + ext))

    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
        for ext in exts:
            paths.append(os.path.join(base, icon_name + ext))

    return paths