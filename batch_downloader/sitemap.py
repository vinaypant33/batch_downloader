"""Read a site's sitemap.xml to find pages a link crawl might miss."""

import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import requests

from .urls import normalize

NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
