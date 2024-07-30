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

    def test_long_names_keep_their_extension(self):
        name = safe_filename("https://s.com/" + "a" * 300 + ".pdf")
        self.assertEqual(len(name), 150)
        self.assertTrue(name.endswith(".pdf"))

    def test_unique_path_numbers_copies(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "r.pdf").write_bytes(b"1")
        (folder / "r (1).pdf").write_bytes(b"2")
        self.assertEqual(unique_path(folder / "r.pdf").name, "r (2).pdf")
        self.assertEqual(unique_path(folder / "new.pdf").name, "new.pdf")


class TestDownloader(unittest.TestCase):
    def setUp(self):
        self.server = TestServer().__enter__()
        self.folder = Path(tempfile.mkdtemp())

    def tearDown(self):
        self.server.__exit__()

    def make(self, **kwargs):
        kwargs.setdefault("backoff", 0)
        return Downloader(self.folder, **kwargs)

    def test_download_saves_exact_bytes_in_category_folder(self):
        result = self.make().download(found(self.server, "docs/report.pdf"))
        self.assertEqual(result.status, "downloaded")
        saved = Path(result.path)
        self.assertEqual(saved, self.folder / "documents" / "report.pdf")
        self.assertEqual(saved.read_bytes(), (SITE / "docs" / "report.pdf").read_bytes())
        self.assertEqual(result.sha256, hashlib.sha256(saved.read_bytes()).hexdigest())
