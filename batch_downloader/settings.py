"""Remembers the user's choices between runs (a small JSON file)."""

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .filetypes import CATEGORIES

DEFAULT_PATH = Path.home() / ".batch_downloader.json"
DEFAULT_FOLDER = str(Path.home() / "Downloads" / "batch_downloader")


@dataclass
class Settings:
    last_url: str = ""
    folder: str = DEFAULT_FOLDER
    categories: list = field(default_factory=lambda: ["documents", "images"])
    depth: int = 1
    delay: float = 0.5
    workers: int = 4
    speed_limit_kb: int = 0        # 0 = unlimited
    respect_robots: bool = True
    same_site_only: bool = True
    use_sitemap: bool = False
    subfolders: bool = True
    include: str = ""              # comma separated patterns, e.g. "*report*, *2024*"
    exclude: str = ""
    max_size_mb: int = 0           # 0 = no limit
    theme: str = "dark"
