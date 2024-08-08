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
