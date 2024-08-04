"""Remembers the user's choices between runs (a small JSON file)."""

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .filetypes import CATEGORIES

DEFAULT_PATH = Path.home() / ".batch_downloader.json"
DEFAULT_FOLDER = str(Path.home() / "Downloads" / "batch_downloader")
