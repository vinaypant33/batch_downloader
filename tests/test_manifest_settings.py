import csv
import json
import tempfile
import unittest
from pathlib import Path

from batch_downloader.crawler import FoundFile
from batch_downloader.downloader import DownloadResult
from batch_downloader.manifest import FILE_NAME, Manifest
from batch_downloader.settings import Settings, load_settings, save_settings


def result(url, status="downloaded", size=10, sha="aa", path="/x"):
    return DownloadResult(url, status, path, size, sha)


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.manifest = Manifest(self.folder)

    def tearDown(self):
        self.manifest.close()

    def test_database_lives_in_the_download_folder(self):
        self.assertTrue((self.folder / FILE_NAME).exists())

    def test_record_and_history(self):
        found = FoundFile("https://s.com/a.pdf", "documents", "https://s.com/", 0)
        self.manifest.record(result("https://s.com/a.pdf"), found)
        self.manifest.record(result("https://s.com/b.pdf", status="failed", size=0, sha=None))
        history = self.manifest.history()
        self.assertEqual([h["url"] for h in history], ["https://s.com/b.pdf", "https://s.com/a.pdf"])
        self.assertEqual(history[1]["category"], "documents")
        self.assertEqual(history[1]["page"], "https://s.com/")

    def test_path_for_hash(self):
        self.manifest.record(result("https://s.com/a.pdf", sha="abc", path="/files/a.pdf"))
        self.assertEqual(self.manifest.path_for_hash("abc"), "/files/a.pdf")
        self.assertIsNone(self.manifest.path_for_hash("abc", exclude_url="https://s.com/a.pdf"))
        self.assertIsNone(self.manifest.path_for_hash("zzz"))
