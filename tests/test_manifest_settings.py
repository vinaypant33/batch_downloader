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

    def test_summary(self):
        self.manifest.record(result("u1", size=100))
        self.manifest.record(result("u2", size=50))
        self.manifest.record(result("u3", status="failed", size=0))
        self.assertEqual(self.manifest.summary(),
                         {"downloaded": {"files": 2, "bytes": 150}, "failed": {"files": 1, "bytes": 0}})

    def test_export_csv_oldest_first(self):
        self.manifest.record(result("first"))
        self.manifest.record(result("second"))
        out = self.folder / "report.csv"
        self.assertEqual(self.manifest.export_csv(out), 2)
        with open(out, newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual([r["url"] for r in rows], ["first", "second"])
        self.assertEqual(list(rows[0]), list(Manifest.COLUMNS))

    def test_history_survives_reopening(self):
        self.manifest.record(result("kept"))
        self.manifest.close()
        self.manifest = Manifest(self.folder)
        self.assertEqual(self.manifest.history()[0]["url"], "kept")


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.mkdtemp()) / "settings.json"

    def test_round_trip(self):
        s = Settings(last_url="https://s.com", depth=3, categories=["videos"], theme="light")
        save_settings(s, self.path)
        loaded = load_settings(self.path)
        self.assertEqual((loaded.last_url, loaded.depth, loaded.categories, loaded.theme),
                         ("https://s.com", 3, ["videos"], "light"))

    def test_missing_or_broken_file_gives_defaults(self):
        self.assertEqual(load_settings(self.path), Settings())
        self.path.write_text("{not json", encoding="utf-8")
        self.assertEqual(load_settings(self.path), Settings())

    def test_bad_values_are_clamped(self):
        self.path.write_text(json.dumps({"depth": 99, "workers": 0, "delay": -3, "categories": ["nope"],
                                         "theme": "pink", "unknown_key": 1}), encoding="utf-8")
        s = load_settings(self.path)
        self.assertEqual((s.depth, s.workers, s.delay, s.categories, s.theme), (5, 1, 0.0, ["documents"], "dark"))
