"""Which files to keep: by type, by name pattern and by size."""

import fnmatch
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

from .filetypes import CATEGORIES, category_of


@dataclass(frozen=True)
class FileFilter:
    categories: frozenset = field(default_factory=lambda: frozenset(CATEGORIES))
    include: tuple = ()        # e.g. ("*report*",) - keep only matching names
    exclude: tuple = ()        # e.g. ("*thumb*",) - drop matching names
    min_bytes: int = 0
    max_bytes: int = 0         # 0 means no limit

    def __post_init__(self):
        unknown = set(self.categories) - set(CATEGORIES)
        if unknown:
            raise ValueError(f"unknown file categories: {', '.join(sorted(unknown))}")
        if self.min_bytes < 0 or self.max_bytes < 0:
            raise ValueError("size limits cannot be negative")
        if self.max_bytes and self.min_bytes > self.max_bytes:
            raise ValueError("min_bytes is larger than max_bytes")
