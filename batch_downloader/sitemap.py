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
