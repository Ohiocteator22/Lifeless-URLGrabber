import threading

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False


_ICON = None
_THREAD = None


def is_available():
    return HAS_PYSTRAY


def _default_icon_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((4, 4, 60, 60), radius=14, fill=(124, 92, 255, 255))
    d.rectangle((28, 16, 36, 38), fill=(255, 255, 255, 255))
    d.polygon([(20, 36), (44, 36), (32, 52)], fill=(255, 255, 255, 255))
    return img


def start(app, on_new_download=None, on_show=None, on_quit=None):
    global _ICON, _THREAD

    if not HAS_PYSTRAY:
        return False
    if _ICON is not None:
        return True

    try:
        image = _default_icon_image()
    except Exception:
        return False

    def _do_show(icon, item):
        if on_show:
            app.after(0, on_show)

    def _do_new(icon, item):
        if on_new_download:
            app.after(0, on_new_download)

    def _do_quit(icon, item):
        try:
            icon.stop()
        finally:
            if on_quit:
                app.after(0, on_quit)
            else:
                app.after(0, app.destroy)

    menu = pystray.Menu(
        pystray.MenuItem("Show URLGrab", _do_show, default=True),
        pystray.MenuItem("New download", _do_new),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", _do_quit),
    )

    _ICON = pystray.Icon("URLGrab", image, "URLGrab", menu)

    def _run():
        try:
            _ICON.run()
        except Exception:
            pass

    _THREAD = threading.Thread(target=_run, daemon=True)
    _THREAD.start()
    return True


def stop():
    global _ICON, _THREAD
    if _ICON is not None:
        try:
            _ICON.stop()
        except Exception:
            pass
        _ICON = None
    _THREAD = None