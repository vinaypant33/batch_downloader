import hashlib
import tempfile
import unittest
from pathlib import Path

from batch_downloader.crawler import FoundFile
from batch_downloader.downloader import Downloader, safe_filename, sha256_of, unique_path
from batch_downloader.filters import FileFilter
from batch_downloader.manifest import Manifest
from batch_downloader.ratelimit import TokenBucket
from tests.server import SITE, TestServer


def found(server, path, category="documents"):
    return FoundFile(server.base + path, category, server.base, 0)


class TestFileNames(unittest.TestCase):
    def test_name_comes_from_the_url(self):
        self.assertEqual(safe_filename("https://s.com/a/Annual%20Report.pdf?x=1"), "Annual Report.pdf")

    def test_illegal_characters_are_replaced(self):
        self.assertEqual(safe_filename('https://s.com/a%3Ab%22c%7Cd.pdf'), "a_b_c_d.pdf")

    def test_reserved_and_empty_names(self):
        self.assertEqual(safe_filename("https://s.com/CON.pdf"), "_CON.pdf")
        self.assertEqual(safe_filename("https://s.com/"), "download")
