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

    def test_filter_is_applied_while_crawling(self):
        _, files = self.crawl(depth=1, file_filter=FileFilter(categories=frozenset({"documents"}),
                                                              exclude=("*summary*",)))
        self.assertEqual(paths(files), ["docs/report.pdf"])

    def test_found_file_records_page_and_depth(self):
        _, files = self.crawl(depth=2)
        deep = next(f for f in files if f.url.endswith("deep.pdf"))
        self.assertTrue(deep.page.endswith("blog/page3.html"))
        self.assertEqual(deep.depth, 2)
        self.assertEqual(deep.category, "documents")

    def test_callbacks_and_stop(self):
        pages, found = [], []
        crawler = Crawler(self.server.base, depth=2, delay=0)
        crawler.crawl(on_page=lambda u, d: pages.append(d), on_file=found.append,
                      should_stop=lambda: len(pages) >= 1)
        self.assertEqual(pages, [0])
        self.assertEqual(len(found), 5)

    def test_max_pages(self):
        crawler, _ = self.crawl(depth=5, max_pages=2)
        self.assertEqual(crawler.stats.pages, 2)

    def test_missing_page_counts_as_error(self):
        crawler = Crawler(self.server.base + "nope.html", depth=0, delay=0)
        self.assertEqual(crawler.crawl(), [])
        self.assertEqual(crawler.stats.errors, 1)

    def test_bad_settings(self):
        with self.assertRaises(ValueError):
            Crawler("not a url")
        with self.assertRaises(ValueError):
            Crawler(self.server.base, depth=-1)


class TestRobotsAndSitemap(unittest.TestCase):
    def test_robots_cache_reads_once_per_site(self):
        with TestServer() as server:
            robots = RobotsCache(requests.Session(), "TestBot")
            self.assertFalse(robots.allowed(server.base + "private/x.pdf"))
            self.assertTrue(robots.allowed(server.base + "docs/x.pdf"))
            self.assertEqual(server.requests["/robots.txt"], 1)

    def test_missing_robots_allows_everything(self):
        robots = RobotsCache(requests.Session(), "TestBot")
        self.assertTrue(robots.allowed("http://127.0.0.1:9/anything"))   # nothing listening

    def test_parse_sitemap(self):
        xml = """<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                 <url><loc>https://s.com/a.html</loc></url><url><loc>https://s.com/b.html</loc></url></urlset>"""
        self.assertEqual(parse_sitemap(xml), (["https://s.com/a.html", "https://s.com/b.html"], []))
        index = """<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                   <sitemap><loc>https://s.com/s1.xml</loc></sitemap></sitemapindex>"""
        self.assertEqual(parse_sitemap(index), ([], ["https://s.com/s1.xml"]))
        self.assertEqual(parse_sitemap("not xml"), ([], []))

    def test_sitemap_adds_unlinked_pages(self):
        with TestServer() as server:
            pages = sitemap_pages(requests.Session(), server.base)
            self.assertTrue(any(p.endswith("hidden.html") for p in pages))
            crawler = Crawler(server.base, depth=1, delay=0, use_sitemap=True)
            files = crawler.crawl()
            self.assertIn("docs/hidden.pdf", paths(files))


if __name__ == "__main__":
    unittest.main()
