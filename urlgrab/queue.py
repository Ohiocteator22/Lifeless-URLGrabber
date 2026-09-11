import threading
import time
import uuid
from datetime import datetime

from . import downloader


STATUS_PENDING     = "pending"
STATUS_DOWNLOADING = "downloading"
STATUS_DONE        = "done"
STATUS_ERROR       = "error"
STATUS_CANCELLED   = "cancelled"

DEFAULT_HEIGHT = 1080


class QueueManager:
    def __init__(self, on_update=None, on_item_done=None):
        self.items = []
        self._lock = threading.Lock()
        self._worker = None
        self._stop_flag = False
        self.on_update = on_update or (lambda: None)
        self.on_item_done = on_item_done or (lambda item: None)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add(self, url, title="Pending…", height=None,
            container="mp4", out_dir=None):
        item = {
            "id": str(uuid.uuid4()),
            "url": url,
            "title": title,
            "height": height,
            "container": container,
            "out_dir": out_dir,
            "status": STATUS_PENDING,
            "progress": 0.0,
            "error": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        with self._lock:
            self.items.append(item)
        self.on_update()
        return item["id"]

    def remove(self, item_id):
        with self._lock:
            self.items = [i for i in self.items if i["id"] != item_id]
        self.on_update()

    def clear_done(self):
        with self._lock:
            self.items = [
                i for i in self.items
                if i["status"] not in (
                    STATUS_DONE, STATUS_ERROR, STATUS_CANCELLED
                )
            ]
        self.on_update()

    def clear_all(self):
        self.stop()
        with self._lock:
            self.items = []
        self.on_update()

    def is_running(self):
        return self._worker is not None and self._worker.is_alive()

    def start(self, cookie_opts=None, default_out_dir=None,
              default_height=DEFAULT_HEIGHT, concurrency=1):
        if self.is_running():
            return
        self._stop_flag = False
        self._worker = threading.Thread(
            target=self._run,
            args=(
                cookie_opts or {},
                default_out_dir,
                default_height,
                max(1, min(int(concurrency or 1), 8)),
            ),
            daemon=True,
        )
        self._worker.start()

    def stop(self):
        self._stop_flag = True

    # ------------------------------------------------------------------
    # Worker pool
    # ------------------------------------------------------------------
    def _claim_next_pending(self):
        """Atomically pick a pending item and mark it as downloading."""
        with self._lock:
            for item in self.items:
                if item["status"] == STATUS_PENDING:
                    item["status"] = STATUS_DOWNLOADING
                    item["progress"] = 0.0
                    item["error"] = None
                    return item
        return None

    def _has_pending(self):
        with self._lock:
            return any(i["status"] == STATUS_PENDING for i in self.items)

    def _run(self, cookie_opts, default_out_dir, default_height, concurrency):
        active = []

        while not self._stop_flag:
            # Clean finished workers
            active = [t for t in active if t.is_alive()]

            # Start new ones while we have free slots
            while len(active) < concurrency and not self._stop_flag:
                item = self._claim_next_pending()
                if not item:
                    break
                t = threading.Thread(
                    target=self._process,
                    args=(
                        item,
                        cookie_opts,
                        default_out_dir,
                        default_height,
                    ),
                    daemon=True,
                )
                t.start()
                active.append(t)
                self.on_update()

            # Nothing running and nothing left to pick up → done
            if not active and not self._has_pending():
                break

            time.sleep(0.15)

        # Wait for currently running workers to finish
        for t in active:
            t.join()

        self.on_update()

    # ------------------------------------------------------------------
    # Per-item processing
    # ------------------------------------------------------------------
    def _process(self, item, cookie_opts, default_out_dir, default_height):
        # Item is already marked as downloading by _claim_next_pending

        if not item.get("height"):
            try:
                info = downloader.fetch_formats(item["url"], cookie_opts)
                item["title"] = info.get("title") or item["title"]
                formats = downloader.filter_and_sort_formats(
                    info.get("formats", [])
                )
                if formats:
                    target = default_height
                    pick = None
                    for f in formats:
                        if f["height"] <= target:
                            pick = f
                            break
                    if pick is None:
                        pick = formats[-1]
                    item["height"] = pick["height"]
                else:
                    item["height"] = default_height
            except Exception as e:
                item["status"] = STATUS_ERROR
                item["error"] = str(e)
                self.on_update()
                return

        def hook(d):
            if d["status"] == "downloading":
                pct_str = d.get("_percent_str", "0%").strip().replace("%", "")
                try:
                    item["progress"] = float(pct_str)
                except ValueError:
                    item["progress"] = 0.0
                self.on_update()
            elif d["status"] == "finished":
                item["progress"] = 100.0
                self.on_update()

        try:
            format_selector = downloader.build_format_selector(item["height"])
            ydl_opts = downloader.build_ydl_opts(
                format_selector=format_selector,
                out_dir=item["out_dir"] or default_out_dir,
                merge_ext=item["container"],
                cookie_opts=cookie_opts,
                progress_hook=hook,
            )
            downloader.download(item["url"], ydl_opts)
            item["status"] = STATUS_DONE
            item["progress"] = 100.0
            self.on_item_done(item)
        except Exception as e:
            item["status"] = STATUS_ERROR
            item["error"] = str(e)

        self.on_update()