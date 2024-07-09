"""
Finds downloadable files on a website.

Breadth-first crawl from a start page:
  depth 0  only the start page
  depth 1  the start page and the pages it links to
  depth N  N levels of links
Every page is checked against robots.txt, the crawler stays on the start
site unless told otherwise, and it waits between page requests.
"""

import logging
import time
from collections import deque
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from .filetypes import category_of
from .filters import FileFilter
from .robots import RobotsCache
from .sitemap import sitemap_pages
from .urls import looks_like_page, normalize, same_site

USER_AGENT = "BatchDownloader/1.0 (+https://github.com/vinaypant33/batch_downloader)"
log = logging.getLogger(__name__)


@dataclass(frozen=True)
class FoundFile:
    url: str
    category: str
    page: str       # the page the link was found on
    depth: int


@dataclass
class CrawlStats:
    pages: int = 0
    files: int = 0
    skipped_robots: int = 0
    skipped_offsite: int = 0
    errors: int = 0
