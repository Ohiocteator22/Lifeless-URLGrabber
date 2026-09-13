import json
import threading
import time
import uuid
from datetime import datetime

from . import downloader
from . import logger


STATUS_PENDING     = "pending"
STATUS_DOWNLOADING = "downloading"
STATUS_DONE        = "done"
STATUS_ERROR       = "error"
STATUS_CANCELLED   = "cancelled"

DEFAULT_HEIGHT = 1080
DEFAULT_CONTAINER = "mp4"


def _new_item(url, title="Pending…", height=None,
              container=DEFAULT_CONTAINER, out_dir=None,
              priority=0, retries_left=2):
    return {
        "id": str(uuid.uuid4()),
        "url": url,
        "title": title,
        "height": height,
        "manual_height": None,
        "container": container,
        "out_dir": out_dir,
        "status": STATUS_PENDING,
        "progress": 0.0,
        "error": None,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "created_at": time.time(),
        "priority": int(priority or 0),
        "paused": False,
        "retries_left": int(retries_left),
    }


class QueueManager:
    def __init__(self, on_update=None, on_item_done=None):
        self.items = []
        self._lock = threading.Lock()
        self._worker = None
        self._stop_flag = False
        self._global_pause = False
        self.auto_retry = 2
        self.on_update = on_update or (lambda: None)
        self.on_item_done = on_item_done or (lambda item: None)

    # ------------------------------------------------------------------
    # Add / remove
    # ------------------------------------------------------------------
    def add(self, url, title="Pending…", height=None,
            container=DEFAULT_CONTAINER, out_dir=None,
            priority=0, retries_left=2):
        item = _new_item(
            url,
            title=title,
            height=height,
            container=container,
            out_dir=out_dir,
            priority=priority,
            retries_left=retries_left,
        )
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

    def find(self, item_id):
        for item in self.items:
            if item["id"] == item_id:
                return item
        return None

    def update_item(self, item_id, updates):
        with self._lock:
            for item in self.items:
                if item["id"] == item_id:
                    for k, v in updates.items():
                        if k in item:
                            item[k] = v
                    break
        self.on_update()

    def reorder(self, item_id, direction):
        """direction: -1 for up, +1 for down. Moves item within the list."""
        with self._lock:
            for idx, item in enumerate(self.items):
                if item["id"] == item_id:
                    new_idx = idx + direction
                    if new_idx < 0 or new_idx >= len(self.items):
                        return
                    self.items[idx], self.items[new_idx] = (
                        self.items[new_idx],
                        self.items[idx],
                    )
                    break
        self.on_update()

    # ------------------------------------------------------------------
    # Pause / resume
    # ------------------------------------------------------------------
    def pause_all(self):
        self._global_pause = True
        self.on_update()

    def resume_all(self):
        self._global_pause = False
        self.on_update()

    def is_paused(self):
        return self._global_pause

    def pause_item(self, item_id):
        with self._lock:
            for item in self.items:
                if item["id"] == item_id and item["status"] == STATUS_PENDING:
                    item["paused"] = True
                    break
        self.on_update()

    def resume_item(self, item_id):
        with self._lock:
            for item in self.items:
                if item["id"] == item_id and item["status"] == STATUS_PENDING:
                    item["paused"] = False
                    break
        self.on_update()

    # ------------------------------------------------------------------
    # Retry
    # ------------------------------------------------------------------
    def retry_item(self, item_id, retries=None):
        if retries is None:
            retries = self.auto_retry
        with self._lock:
            for item in self.items:
                if item["id"] == item_id and item["status"] in (
                    STATUS_ERROR, STATUS_CANCELLED
                ):
                    item["status"] = STATUS_PENDING
                    item["progress"] = 0.0
                    item["error"] = None
                    item["retries_left"] = int(retries)
                    item["paused"] = False
                    break
        self.on_update()

    def retry_all_failed(self, retries=None):
        if retries is None:
            retries = self.auto_retry
        with self._lock:
            for item in self.items:
                if item["status"] in (STATUS_ERROR, STATUS_CANCELLED):
                    item["status"] = STATUS_PENDING
                    item["progress"] = 0.0
                    item["error"] = None
                    item["retries_left"] = int(retries)
                    item["paused"] = False
        self.on_update()

    # ------------------------------------------------------------------
    # Import / export
    # ------------------------------------------------------------------
    def export_to(self, path):
        with self._lock:
            snapshot = [dict(i) for i in self.items]
        # Strip volatile fields so imports are cleaner
        for item in snapshot:
            item.pop("progress", None)
            item.pop("error", None)
            if item.get("status") == STATUS_DOWNLOADING:
                item["status"] = STATUS_PENDING
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            logger.append(f"Queue exported to {path}")
            return True
        except Exception as e:
            logger.append(f"Queue export failed: {e}", "ERROR")
            return False

    def import_from(self, path, merge=True):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return False
        except Exception as e:
            logger.append(f"Queue import failed: {e}", "ERROR")
            return False

        imported = []
        for raw in data:
            if not isinstance(raw, dict) or not raw.get("url"):
                continue
            item = _new_item(
                raw["url"],
                title=raw.get("title", "Pending…"),
                height=raw.get("height"),
                container=raw.get("container", DEFAULT_CONTAINER),
                out_dir=raw.get("out_dir"),
                priority=raw.get("priority", 0),
                retries_left=raw.get("retries_left", self.auto_retry),
            )
            if raw.get("manual_height"):
                item["manual_height"] = raw["manual_height"]
            imported.append(item)

        with self._lock:
            if merge:
                self.items.extend(imported)
            else:
                self.items = imported
        logger.append(f"Imported {len(imported)} queue item(s)")
        self.on_update()
        return True

    # ------------------------------------------------------------------
    # Run control
    # ------------------------------------------------------------------
    def is_running(self):
        return self._worker is not None and self._worker.is_alive()

    def start(self, cookie_opts=None, default_out_dir=None,
              default_height=DEFAULT_HEIGHT, concurrency=1,
              net_opts=None, auto_retry=None):
        if self.is_running():
            return
        if auto_retry is not None:
            self.auto_retry = int(auto_retry)
        self._stop_flag = False
        self._worker = threading.Thread(
            target=self._run,
            args=(
                cookie_opts or {},
                default_out_dir,
                default_height,
                max(1, min(int(concurrency or 1), 8)),
                net_opts or {},
            ),
            daemon=True,
        )
        self._worker.start()

    def stop(self):
        self._stop_flag = True

    # ------------------------------------------------------------------
    # Worker
    # ------------------------------------------------------------------
    def _claim_next_pending(self):
        with self._lock:
            candidates = [
                i for i in self.items
                if i["status"] == STATUS_PENDING and not i.get("paused", False)
            ]
            if not candidates:
                return None
            candidates.sort(
                key=lambda x: (
                    -int(x.get("priority", 0)),
                    x.get("created_at", 0.0),
                )
            )
            item = candidates[0]
            item["status"] = STATUS_DOWNLOADING
            item["progress"] = 0.0
            item["error"] = None
            return item

    def _has_pending(self):
        with self._lock:
            return any(
                i["status"] == STATUS_PENDING and not i.get("paused", False)
                for i in self.items
            )

    def _run(self, cookie_opts, default_out_dir, default_height,
             concurrency, net_opts):
        active = []

        while not self._stop_flag:
            if self._global_pause:
                time.sleep(0.2)
                continue

            active = [t for t in active if t.is_alive()]

            while len(active) < concurrency and not self._stop_flag:
                if self._global_pause:
                    break
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
                        net_opts,
                    ),
                    daemon=True,
                )
                t.start()
                active.append(t)
                self.on_update()

            if not active and not self._has_pending():
                break

            time.sleep(0.15)

        for t in active:
            t.join()

        self.on_update()

    def _process(self, item, cookie_opts, default_out_dir,
                 default_height, net_opts):
        # Resolve metadata if we don't know the height yet
        if not item.get("height") and not item.get("manual_height"):
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
                self._handle_error(item, str(e))
                return

        # Manual override wins
        target_height = item.get("manual_height") or item.get("height")
        if not target_height:
            target_height = default_height

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
            format_selector = downloader.build_format_selector(target_height)
            ydl_opts = downloader.build_ydl_opts(
                format_selector=format_selector,
                out_dir=item["out_dir"] or default_out_dir,
                merge_ext=item["container"],
                cookie_opts=cookie_opts,
                progress_hook=hook,
                net_opts=net_opts,
            )
            downloader.download(item["url"], ydl_opts)
            item["status"] = STATUS_DONE
            item["progress"] = 100.0
            self.on_item_done(item)
        except Exception as e:
            self._handle_error(item, str(e))

        self.on_update()

    def _handle_error(self, item, err):
        item["error"] = err
        left = int(item.get("retries_left", 0))
        if left > 0 and not self._stop_flag:
            item["retries_left"] = left - 1
            item["status"] = STATUS_PENDING
            item["progress"] = 0.0
            logger.append(
                f"Retrying {item.get('title', 'item')} "
                f"({left - 1} retries left): {err[:80]}",
                "WARNING",
            )
        else:
            item["status"] = STATUS_ERROR
            logger.append(
                f"Queue item failed: {err[:120]}",
                "ERROR",
            )