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
