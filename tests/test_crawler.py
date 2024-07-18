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


class TestCrawler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = TestServer().__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.server.__exit__()

    def crawl(self, **kwargs):
        kwargs.setdefault("delay", 0)
        crawler = Crawler(self.server.base, **kwargs)
        return crawler, crawler.crawl()

    def test_depth_zero_is_only_the_start_page(self):
        crawler, files = self.crawl(depth=0)
        self.assertEqual(paths(files), ["docs/Annual%20Summary.pdf", "docs/report.pdf", "img/logo.png",
                                        "img/logo@2x.png", "media/clip.mp4"])
        self.assertEqual(crawler.stats.pages, 1)

    def test_each_depth_finds_more(self):
        counts = [len(self.crawl(depth=d)[1]) for d in (0, 1, 2)]
        self.assertEqual(counts, [5, 8, 9])

    def test_files_are_found_once(self):
        _, files = self.crawl(depth=2)
        urls = [f.url for f in files]
        self.assertEqual(len(urls), len(set(urls)))

    def test_offsite_links_are_skipped_by_default(self):
        crawler, files = self.crawl(depth=1)
        self.assertNotIn("outside.zip", " ".join(f.url for f in files))
        self.assertGreaterEqual(crawler.stats.skipped_offsite, 1)

    def test_offsite_files_can_be_allowed(self):
        _, files = self.crawl(depth=0, offsite_files=True)
        self.assertIn("https://other-site.example/files/outside.zip", [f.url for f in files])

    def test_robots_txt_is_respected(self):
        crawler, files = self.crawl(depth=0)
        self.assertNotIn("private/secret.pdf", paths(files))
        self.assertEqual(crawler.stats.skipped_robots, 1)
        _, files = self.crawl(depth=0, respect_robots=False)
        self.assertIn("private/secret.pdf", paths(files))
