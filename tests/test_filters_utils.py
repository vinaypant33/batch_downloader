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

    def test_invalid_filters_are_rejected(self):
        with self.assertRaises(ValueError):
            FileFilter(categories=frozenset({"spreadsheets"}))
        with self.assertRaises(ValueError):
            FileFilter(min_bytes=10, max_bytes=5)
        with self.assertRaises(ValueError):
            FileFilter(max_bytes=-1)


class TestUtils(unittest.TestCase):
    def test_human_size(self):
        self.assertEqual(human_size(512), "512 B")
        self.assertEqual(human_size(1536), "1.5 KB")
        self.assertEqual(human_size(5 * 1024 ** 3), "5.0 GB")
        self.assertEqual(human_size(None), "?")

    def test_shorten(self):
        self.assertEqual(shorten("short", 10), "short")
        long = "https://example.com/" + "x" * 100 + "/file.pdf"
        out = shorten(long, 40)
        self.assertEqual(len(out), 40)
        self.assertTrue(out.endswith("file.pdf"))


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.slept = 0.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.slept += seconds
        self.now += seconds


class TestTokenBucket(unittest.TestCase):
    def test_burst_is_free_then_rate_applies(self):
        clock = FakeClock()
        bucket = TokenBucket(1000, clock=clock.time, sleep=clock.sleep)
        self.assertEqual(bucket.consume(1000), 0.0)
        self.assertAlmostEqual(bucket.consume(500), 0.5)

    def test_average_rate_over_many_chunks(self):
        clock = FakeClock()
        bucket = TokenBucket(2000, clock=clock.time, sleep=clock.sleep)
        for _ in range(20):
            bucket.consume(1000)
        self.assertAlmostEqual(clock.now, 9.0)   # 20 KB at 2 KB/s, first 2 KB free
