import unittest

import requests

from batch_downloader.crawler import Crawler, extract_links
from batch_downloader.filters import FileFilter
from batch_downloader.robots import RobotsCache
from batch_downloader.sitemap import parse_sitemap, sitemap_pages
from tests.server import TestServer


def paths(files):
    return sorted(f.url.split("/", 3)[3] for f in files)


class TestExtractLinks(unittest.TestCase):
    def test_reads_all_link_attributes(self):
        html = """<a href="a.pdf"></a><img src="b.png"><video src="c.mp4"></video>
                  <audio src="d.mp3"></audio><source src="e.webm"><object data="f.pdf"></object>"""
        links = extract_links(html, "https://s.com/")
        self.assertEqual(sorted(l.rsplit("/", 1)[1] for l in links),
                         ["a.pdf", "b.png", "c.mp4", "d.mp3", "e.webm", "f.pdf"])

    def test_srcset_base_tag_and_duplicates(self):
        html = """<base href="/files/"><img srcset="x.png 1x, x@2x.png 2x"><a href="x.png">again</a>"""
        links = extract_links(html, "https://s.com/page/")
        self.assertEqual(links, ["https://s.com/files/x.png", "https://s.com/files/x@2x.png"])
