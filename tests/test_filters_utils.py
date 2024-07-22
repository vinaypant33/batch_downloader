import unittest

from batch_downloader.filetypes import CATEGORIES, category_of, extension_of
from batch_downloader.filters import FileFilter
from batch_downloader.ratelimit import TokenBucket
from batch_downloader.utils import human_size, shorten


class TestFileTypes(unittest.TestCase):
    def test_extension_ignores_case_query_and_encoding(self):
        self.assertEqual(extension_of("https://s.com/a/Report%20Final.PDF?x=1"), ".pdf")
        self.assertEqual(extension_of("https://s.com/folder/"), "")

    def test_categories(self):
        self.assertEqual(category_of("https://s.com/clip.MP4"), "videos")
        self.assertEqual(category_of("https://s.com/song.mp3"), "audio")
        self.assertEqual(category_of("https://s.com/pic.jpeg"), "images")
        self.assertEqual(category_of("https://s.com/data.tar.gz"), "archives")
        self.assertIsNone(category_of("https://s.com/page.html"))

    def test_no_extension_is_in_two_categories(self):
        seen = [ext for exts in CATEGORIES.values() for ext in exts]
        self.assertEqual(len(seen), len(set(seen)))


class TestFileFilter(unittest.TestCase):
    def test_category_filter(self):
        f = FileFilter(categories=frozenset({"documents"}))
        self.assertTrue(f.accepts_url("https://s.com/a.pdf"))
        self.assertFalse(f.accepts_url("https://s.com/a.png"))

    def test_include_and_exclude_patterns(self):
        f = FileFilter(include=("*report*",), exclude=("*draft*",))
        self.assertTrue(f.accepts_url("https://s.com/Annual-Report.pdf"))
        self.assertFalse(f.accepts_url("https://s.com/report-draft.pdf"))
        self.assertFalse(f.accepts_url("https://s.com/summary.pdf"))

    def test_size_limits(self):
        f = FileFilter(min_bytes=10, max_bytes=100)
        self.assertTrue(f.accepts_size(50))
        self.assertTrue(f.accepts_size(None))      # unknown size is allowed
        self.assertFalse(f.accepts_size(5))
        self.assertFalse(f.accepts_size(500))
        self.assertTrue(FileFilter().accepts_size(10 ** 12))
