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


class Downloader:
    def __init__(self, folder, session=None, subfolders=True, file_filter=None, timeout=30,
                 retries=2, backoff=1.0, chunk_size=64 * 1024, rate_limiter=None, manifest=None,
                 resume=True):
        self.folder = Path(folder)
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.subfolders = subfolders
        self.filter = file_filter or FileFilter()
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.chunk_size = chunk_size
        self.rate_limiter = rate_limiter
        self.manifest = manifest
        self.resume = resume

    def target_for(self, found):
        folder = self.folder / found.category if self.subfolders else self.folder
        return folder / safe_filename(found.url)

    def download(self, found, on_progress=None, should_stop=None):
        """Download one file, retrying network and server errors."""
        should_stop = should_stop or (lambda: False)
        attempt = 0
        while True:
            attempt += 1
            try:
                return self._download_once(found, attempt, on_progress, should_stop)
            except StopRequested:
                return DownloadResult(found.url, "stopped", attempts=attempt)
            except _Retryable as error:
                if attempt > self.retries:
                    log.warning("giving up on %s after %d attempts: %s", found.url, attempt, error)
                    return DownloadResult(found.url, "failed", error=str(error), attempts=attempt)
                log.info("retrying %s (attempt %d failed: %s)", found.url, attempt, error)
                time.sleep(self.backoff * 2 ** (attempt - 1))
            except (requests.RequestException, OSError) as error:
                log.warning("download of %s failed: %s", found.url, error)
                return DownloadResult(found.url, "failed", error=str(error), attempts=attempt)

    def _download_once(self, found, attempt, on_progress, should_stop):
        target = self.target_for(found)
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_name(target.name + ".part")
        have = part.stat().st_size if (self.resume and part.exists()) else 0
        headers = {"Range": f"bytes={have}-"} if have else {}
        try:
            response = self.session.get(found.url, stream=True, timeout=self.timeout, headers=headers)
        except (requests.ConnectionError, requests.Timeout) as error:
            raise _Retryable(str(error)) from error

        with response:
            if response.status_code == 416:            # .part is already complete
                response.close()
                have, total, mode = have, have, None
            elif response.status_code >= 500:
                raise _Retryable(f"HTTP {response.status_code}")
            elif response.status_code >= 400:
                return DownloadResult(found.url, "failed", error=f"HTTP {response.status_code}", attempts=attempt)
            else:
                resumed = response.status_code == 206 and have > 0
                if not resumed:
                    have = 0
                length = response.headers.get("Content-Length")
                total = have + int(length) if length and length.isdigit() else None
                mode = "ab" if resumed else "wb"

            if not self.filter.accepts_size(total):
                return DownloadResult(found.url, "skipped", error="outside the size limits",
                                      size=total or 0, attempts=attempt)
            if target.exists() and total is not None and target.stat().st_size == total:
                part.unlink(missing_ok=True)
                return DownloadResult(found.url, "skipped", str(target), total,
                                      error="already downloaded", attempts=attempt)
