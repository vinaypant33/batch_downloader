import unittest

from batch_downloader.urls import host_of, looks_like_page, normalize, robots_url, same_site


class TestNormalize(unittest.TestCase):
    def test_relative_link_becomes_absolute(self):
        self.assertEqual(normalize("docs/a.pdf", "https://site.com/x/"), "https://site.com/x/docs/a.pdf")

    def test_fragment_is_removed(self):
        self.assertEqual(normalize("https://site.com/a.pdf#page=3"), "https://site.com/a.pdf")

    def test_scheme_and_host_are_lowercased(self):
        self.assertEqual(normalize("HTTPS://Site.COM/Path"), "https://site.com/Path")
