"""
Runs a crawl followed by the downloads on a background thread.

The window must never block, so the job reports everything through a queue of
(kind, payload) events that the window reads a few times a second:

    ("status", text)              what is happening now
    ("page", (url, depth))        a page is being crawled
    ("found", (index, FoundFile)) a file was found
    ("progress", (index, done, total))
    ("result", (index, DownloadResult))
    ("done", summary dict)        always the last event
"""

import logging
import queue
import threading
from collections import Counter
from dataclasses import dataclass, field

from .crawler import Crawler
from .downloader import Downloader
from .filters import FileFilter
from .log import close_logging, setup_logging
from .manifest import Manifest
from .ratelimit import TokenBucket


@dataclass
class JobOptions:
    url: str
    folder: str
    categories: tuple = ("documents", "images")
    depth: int = 1
    delay: float = 0.5
    workers: int = 4
    speed_limit_kb: int = 0
    respect_robots: bool = True
    same_site_only: bool = True
    use_sitemap: bool = False
    subfolders: bool = True
    include: tuple = ()
    exclude: tuple = ()
    max_size_mb: int = 0
    list_only: bool = False
    files: tuple = ()              # given files: skip the crawl (used by "Retry failed")
    session: object = field(default=None, repr=False)


class DownloadJob(threading.Thread):
    def __init__(self, options, events=None):
        super().__init__(daemon=True)
        self.options = options
        self.events = events or queue.Queue()
        self._stop_requested = threading.Event()
        self._unpaused = threading.Event()
        self._unpaused.set()
        self.files = []
        self.results = []

    def stop(self):
        self._stop_requested.set()
        self._unpaused.set()          # wake a paused job so it can stop

    def pause(self):
        self._unpaused.clear()
        self.emit("status", "Paused")

    def resume(self):
        self._unpaused.set()
        self.emit("status", "Resumed")

    @property
    def paused(self):
        return not self._unpaused.is_set()

    def should_stop(self):
        """Called often by the crawler and downloader; blocks while paused."""
        self._unpaused.wait()
        return self._stop_requested.is_set()

    def emit(self, kind, payload=None):
        self.events.put((kind, payload))
