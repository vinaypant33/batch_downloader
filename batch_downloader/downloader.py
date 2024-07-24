"""
Downloads the files the crawler found.

Each file streams into `<name>.part` and is renamed when complete, so a
half-finished file never looks finished. An interrupted download resumes from
the .part file with an HTTP Range request when the server supports it.
Failures caused by the network or a 5xx response are retried with backoff.
"""

import hashlib
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

import requests

from .crawler import USER_AGENT
from .filters import FileFilter

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DownloadResult:
    url: str
    status: str            # downloaded | skipped | duplicate | failed | stopped
    path: str = None
    size: int = 0
    sha256: str = None
    error: str = None
    attempts: int = 1


class StopRequested(Exception):
    """Raised inside a download when the user presses Stop."""


class _Retryable(Exception):
    """A failure worth trying again (network problem or 5xx)."""
