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

    @staticmethod
    def name_of(url):
        return PurePosixPath(unquote(urlparse(url).path)).name.lower()

    def accepts_url(self, url):
        """Type and name checks, done before anything is downloaded."""
        if category_of(url) not in self.categories:
            return False
        name = self.name_of(url)
        if self.include and not any(fnmatch.fnmatch(name, p.lower()) for p in self.include):
            return False
        if any(fnmatch.fnmatch(name, p.lower()) for p in self.exclude):
            return False
        return True

    def accepts_size(self, size):
        """Size check, done once the server says how big a file is."""
        if size is None:
            return True
        if size < self.min_bytes:
            return False
        if self.max_bytes and size > self.max_bytes:
            return False
        return True
