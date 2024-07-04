"""Which files to keep: by type, by name pattern and by size."""

import fnmatch
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

from .filetypes import CATEGORIES, category_of
