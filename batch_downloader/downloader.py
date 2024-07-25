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


INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def safe_filename(url, default="download"):
    """A file name that is safe on Windows, macOS and Linux."""
    name = PurePosixPath(unquote(urlparse(url).path)).name
    name = INVALID_CHARS.sub("_", name).strip(" .")
    if not name:
        name = default
    stem, dot, ext = name.partition(".")
    if stem.upper() in RESERVED_NAMES:
        name = f"_{name}"
    if len(name) > 150:
        suffix = PurePosixPath(name).suffix[:10]
        name = name[:150 - len(suffix)] + suffix
    return name


def unique_path(path):
    """report.pdf -> 'report (1).pdf' if report.pdf already exists."""
    path = Path(path)
    if not path.exists():
        return path
    for n in range(1, 10_000):
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"too many copies of {path.name}")


def sha256_of(path, chunk=1 << 20):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()
