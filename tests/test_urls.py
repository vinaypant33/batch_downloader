import unittest

from batch_downloader.urls import host_of, looks_like_page, normalize, robots_url, same_site


class TestNormalize(unittest.TestCase):
    def test_relative_link_becomes_absolute(self):
        self.assertEqual(normalize("docs/a.pdf", "https://site.com/x/"), "https://site.com/x/docs/a.pdf")
