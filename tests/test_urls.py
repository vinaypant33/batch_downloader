import unittest

from batch_downloader.urls import host_of, looks_like_page, normalize, robots_url, same_site


class TestNormalize(unittest.TestCase):
    def test_relative_link_becomes_absolute(self):
        self.assertEqual(normalize("docs/a.pdf", "https://site.com/x/"), "https://site.com/x/docs/a.pdf")

    def test_fragment_is_removed(self):
        self.assertEqual(normalize("https://site.com/a.pdf#page=3"), "https://site.com/a.pdf")

    def test_scheme_and_host_are_lowercased(self):
        self.assertEqual(normalize("HTTPS://Site.COM/Path"), "https://site.com/Path")

    def test_default_port_is_dropped_other_ports_kept(self):
        self.assertEqual(normalize("https://site.com:443/a"), "https://site.com/a")
        self.assertEqual(normalize("http://site.com:8080/a"), "http://site.com:8080/a")

    def test_non_web_links_are_rejected(self):
        for link in ("mailto:a@b.com", "javascript:void(0)", "ftp://site.com/f", "data:text/plain,hi", "", None):
            with self.subTest(link=link):
                self.assertIsNone(normalize(link, "https://site.com/"))

    def test_empty_path_becomes_slash_and_query_is_kept(self):
        self.assertEqual(normalize("https://site.com"), "https://site.com/")
        self.assertEqual(normalize("/get?id=7", "https://site.com/a/"), "https://site.com/get?id=7")


class TestSites(unittest.TestCase):
    def test_www_is_the_same_site(self):
        self.assertTrue(same_site("https://www.site.com/a", "https://site.com/b"))
        self.assertFalse(same_site("https://site.com/a", "https://other.com/a"))
        self.assertEqual(host_of("http://www.Site.com:8080/x"), "site.com:8080")
