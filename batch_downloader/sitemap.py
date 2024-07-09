"""Read a site's sitemap.xml to find pages a link crawl might miss."""

import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import requests

from .urls import normalize

NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def parse_sitemap(xml_text):
    """Return (page_urls, child_sitemap_urls) from sitemap XML."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return [], []
    tag = root.tag.replace(NS, "")
    locs = [el.text.strip() for el in root.iter(f"{NS}loc") if el.text]
    if not locs:  # sitemaps without the namespace
        locs = [el.text.strip() for el in root.iter("loc") if el.text]
    if tag == "sitemapindex":
        return [], locs
    return locs, []


def sitemap_pages(session, start_url, timeout=10, limit=500):
    """Pages listed in /sitemap.xml (following one level of sitemap index)."""
    pages = []
    to_read = [urljoin(start_url, "/sitemap.xml")]
    read = set()
    while to_read and len(pages) < limit:
        url = to_read.pop(0)
        if url in read:
            continue
        read.add(url)
        try:
            response = session.get(url, timeout=timeout)
        except requests.RequestException:
            continue
        if response.status_code != 200:
            continue
        found, children = parse_sitemap(response.text)
        # entries should be absolute, but resolve relative ones against the sitemap
        pages.extend(u for u in (normalize(p, url) for p in found) if u)
        if len(read) == 1:
            to_read.extend(u for u in (normalize(c, url) for c in children) if u)
    return pages[:limit]
