import unittest

from batch_downloader.filetypes import CATEGORIES, category_of, extension_of
from batch_downloader.filters import FileFilter
from batch_downloader.ratelimit import TokenBucket
from batch_downloader.utils import human_size, shorten


class TestFileTypes(unittest.TestCase):
    def test_extension_ignores_case_query_and_encoding(self):
        self.assertEqual(extension_of("https://s.com/a/Report%20Final.PDF?x=1"), ".pdf")
        self.assertEqual(extension_of("https://s.com/folder/"), "")
