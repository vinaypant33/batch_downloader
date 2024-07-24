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
