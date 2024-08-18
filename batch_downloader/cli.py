"""
Command line version, for scripts and servers without a screen.

    python -m batch_downloader https://example.com/files --types documents images --depth 2
    python -m batch_downloader https://example.com --list
"""

import argparse
import queue
from collections import Counter

from . import __version__
from .filetypes import CATEGORIES
from .jobs import DownloadJob, JobOptions
from .settings import DEFAULT_FOLDER
from .utils import human_size, shorten
