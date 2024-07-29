"""
Download history, stored in SQLite inside the download folder.

Used to show past downloads in the app, to export a CSV report, and to spot
files that are exact duplicates (same SHA-256) of something already saved.
"""

import csv
import sqlite3
import threading
from pathlib import Path

from .utils import now_iso

FILE_NAME = ".batch_downloader.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS downloads (
    id          INTEGER PRIMARY KEY,
    url         TEXT NOT NULL,
    page        TEXT,
    category    TEXT,
    status      TEXT NOT NULL,
    path        TEXT,
    size        INTEGER,
    sha256      TEXT,
    error       TEXT,
    finished_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_downloads_sha ON downloads (sha256);
"""


class Manifest:
    def __init__(self, folder):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / FILE_NAME
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.executescript(SCHEMA)
        self._lock = threading.Lock()

    def close(self):
        self._conn.close()

    def record(self, result, found=None):
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO downloads (url, page, category, status, path, size, sha256, error, finished_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (result.url, getattr(found, "page", None), getattr(found, "category", None), result.status,
                 result.path, result.size, result.sha256, result.error, now_iso()),
            )

    def path_for_hash(self, sha256, exclude_url=None):
        """Where a file with this checksum was already saved, if anywhere."""
        with self._lock:
            row = self._conn.execute(
                "SELECT path FROM downloads WHERE sha256 = ? AND status = 'downloaded' AND url <> ? "
                "ORDER BY id LIMIT 1",
                (sha256, exclude_url or ""),
            ).fetchone()
        return row[0] if row else None

    COLUMNS = ("finished_at", "status", "category", "size", "path", "url", "page", "sha256", "error")

    def history(self, limit=500):
        with self._lock:
            rows = self._conn.execute(
                f"SELECT {', '.join(self.COLUMNS)} FROM downloads ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(zip(self.COLUMNS, row)) for row in rows]

    def summary(self):
        with self._lock:
            rows = self._conn.execute(
                "SELECT status, COUNT(*), COALESCE(SUM(size), 0) FROM downloads GROUP BY status"
            ).fetchall()
        return {status: {"files": count, "bytes": total} for status, count, total in rows}

    def export_csv(self, path):
        rows = self.history(limit=1_000_000)
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.COLUMNS)
            writer.writeheader()
            writer.writerows(reversed(rows))
        return len(rows)
