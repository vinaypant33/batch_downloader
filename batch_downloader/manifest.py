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
