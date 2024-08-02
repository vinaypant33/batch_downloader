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

    def test_flat_folder_option(self):
        result = self.make(subfolders=False).download(found(self.server, "img/logo.png", "images"))
        self.assertEqual(Path(result.path).parent, self.folder)

    def test_second_download_is_skipped(self):
        downloader = self.make()
        downloader.download(found(self.server, "docs/report.pdf"))
        again = downloader.download(found(self.server, "docs/report.pdf"))
        self.assertEqual(again.status, "skipped")
        self.assertEqual(again.error, "already downloaded")

    def test_changed_file_is_saved_as_a_copy(self):
        (self.folder / "documents").mkdir()
        (self.folder / "documents" / "report.pdf").write_bytes(b"an older, different file")
        result = self.make().download(found(self.server, "docs/report.pdf"))
        self.assertEqual(Path(result.path).name, "report (1).pdf")

    def test_no_part_files_left_behind(self):
        self.make().download(found(self.server, "media/clip.mp4", "videos"))
        self.assertEqual(list(self.folder.rglob("*.part")), [])

    def test_missing_file_fails_without_retry(self):
        result = self.make().download(found(self.server, "docs/missing.pdf"))
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error, "HTTP 404")
        self.assertEqual(result.attempts, 1)

    def test_server_errors_are_retried(self):
        self.server.fail("/flaky/docs/report.pdf", times=2)
        result = self.make(retries=2).download(found(self.server, "flaky/docs/report.pdf"))
        self.assertEqual(result.status, "downloaded")
        self.assertEqual(result.attempts, 3)

    def test_retries_give_up(self):
        self.server.fail("/flaky/docs/report.pdf", times=5)
        result = self.make(retries=1).download(found(self.server, "flaky/docs/report.pdf"))
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.attempts, 2)
        self.assertIn("503", result.error)

    def test_resume_from_part_file(self):
        original = (SITE / "media" / "clip.mp4").read_bytes()
        target = self.folder / "videos" / "clip.mp4.part"
        target.parent.mkdir(parents=True)
        target.write_bytes(original[:1000])
        result = self.make().download(found(self.server, "media/clip.mp4", "videos"))
        self.assertEqual(result.status, "downloaded")
        self.assertEqual(Path(result.path).read_bytes(), original)

    def test_resume_falls_back_when_server_ignores_ranges(self):
        self.server.__exit__()
        self.server = TestServer(ranges=False).__enter__()
        original = (SITE / "media" / "clip.mp4").read_bytes()
        part = self.folder / "videos" / "clip.mp4.part"
        part.parent.mkdir(parents=True)
        part.write_bytes(b"garbage that must be thrown away")
        result = self.make().download(found(self.server, "media/clip.mp4", "videos"))
        self.assertEqual(Path(result.path).read_bytes(), original)

    def test_size_limit_skips_big_files(self):
        downloader = self.make(file_filter=FileFilter(max_bytes=1000))
        result = downloader.download(found(self.server, "media/clip.mp4", "videos"))
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.error, "outside the size limits")
        self.assertFalse((self.folder / "videos" / "clip.mp4").exists())

    def test_stop_keeps_part_file_for_later(self):
        calls = []
        result = self.make(chunk_size=512).download(
            found(self.server, "slow/media/clip.mp4", "videos"),
            should_stop=lambda: calls.append(1) or len(calls) > 2)
        self.assertEqual(result.status, "stopped")
        self.assertTrue((self.folder / "videos" / "clip.mp4.part").exists())

    def test_progress_reports_bytes(self):
        seen = []
        self.make(chunk_size=500).download(found(self.server, "docs/report.pdf"),
                                           on_progress=lambda f, done, total: seen.append((done, total)))
        size = (SITE / "docs" / "report.pdf").stat().st_size
        self.assertEqual(seen[-1], (size, size))
        self.assertEqual([d for d, _ in seen], sorted(d for d, _ in seen))
