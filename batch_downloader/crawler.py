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


LINK_ATTRIBUTES = (
    ("a", "href"), ("img", "src"), ("source", "src"), ("video", "src"), ("audio", "src"),
    ("embed", "src"), ("object", "data"), ("link", "href"), ("track", "src"),
)


def extract_links(html, base_url):
    """Every absolute http(s) link on a page, in page order, without repeats."""
    soup = BeautifulSoup(html, "html.parser")
    base_tag = soup.find("base", href=True)
    base = normalize(base_tag["href"], base_url) if base_tag else base_url
    links = []
    for tag, attribute in LINK_ATTRIBUTES:
        for element in soup.find_all(tag):
            value = element.get(attribute)
            if value:
                links.append(value)
    for element in soup.find_all(srcset=True):        # responsive images
        for candidate in element["srcset"].split(","):
            if candidate.strip():
                links.append(candidate.strip().split()[0])
    seen, result = set(), []
    for link in links:
        url = normalize(link, base)
        if url and url not in seen:
            seen.add(url)
            result.append(url)
    return result


class Crawler:
    def __init__(self, start_url, depth=1, file_filter=None, same_site_only=True,
                 offsite_files=False, delay=0.5, max_pages=200, respect_robots=True,
                 use_sitemap=False, session=None, timeout=15, user_agent=USER_AGENT):
        url = normalize(start_url)
        if url is None:
            raise ValueError(f"not a web address: {start_url!r}")
        if depth < 0 or max_pages < 1 or delay < 0:
            raise ValueError("depth and delay must be >= 0 and max_pages >= 1")
        self.start_url = url
        self.depth = depth
        self.filter = file_filter or FileFilter()
        self.same_site_only = same_site_only
        self.offsite_files = offsite_files
        self.delay = delay
        self.max_pages = max_pages
        self.use_sitemap = use_sitemap
        self.timeout = timeout
        self.user_agent = user_agent
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", user_agent)
        self.robots = RobotsCache(self.session, user_agent) if respect_robots else None
        self.stats = CrawlStats()

    def _page_allowed(self, url):
        if self.same_site_only and not same_site(url, self.start_url):
            self.stats.skipped_offsite += 1
            return False
        if self.robots and not self.robots.allowed(url):
            self.stats.skipped_robots += 1
            return False
        return True

    def _file_allowed(self, url):
        if not self.offsite_files and not same_site(url, self.start_url):
            self.stats.skipped_offsite += 1
            return False
        if self.robots and not self.robots.allowed(url):
            self.stats.skipped_robots += 1
            return False
        return self.filter.accepts_url(url)

    def _wait(self, url, first):
        if first:
            return
        delay = self.delay
        if self.robots:
            delay = max(delay, self.robots.crawl_delay(url) or 0)
        if delay:
            time.sleep(delay)
