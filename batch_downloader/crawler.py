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
