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

    def clean(self):
        """Clamp values into their allowed ranges so a hand-edited file cannot break the app."""
        self.categories = [c for c in self.categories if c in CATEGORIES] or ["documents"]
        self.depth = min(max(int(self.depth), 0), 5)
        self.delay = min(max(float(self.delay), 0.0), 10.0)
        self.workers = min(max(int(self.workers), 1), 8)
        self.speed_limit_kb = max(int(self.speed_limit_kb), 0)
        self.max_size_mb = max(int(self.max_size_mb), 0)
        self.theme = self.theme if self.theme in ("dark", "light", "system") else "dark"
        return self

    @staticmethod
    def patterns(text):
        return tuple(p.strip() for p in text.split(",") if p.strip())


def load_settings(path=DEFAULT_PATH):
    """Settings from disk, or defaults if the file is missing or broken."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Settings()
    known = {f.name for f in fields(Settings)}
    try:
        return Settings(**{k: v for k, v in raw.items() if k in known}).clean()
    except (TypeError, ValueError):
        return Settings()


def save_settings(settings, path=DEFAULT_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings.clean()), indent=2), encoding="utf-8")
