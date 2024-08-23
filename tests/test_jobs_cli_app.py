import contextlib
import io
import queue
import tempfile
import tkinter
import unittest
from pathlib import Path

from batch_downloader.app import validate
from batch_downloader.cli import build_parser, main, options_from
from batch_downloader.jobs import DownloadJob, JobOptions
from tests.server import TestServer

ALL = ("documents", "images", "videos", "audio", "archives")


def drain(events):
    out = []
    while True:
        kind, payload = events.get(timeout=30)
        out.append((kind, payload))
        if kind == "done":
            return out


class TestDownloadJob(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = TestServer().__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.server.__exit__()

    def run_job(self, **kwargs):
        options = JobOptions(url=self.server.base, folder=tempfile.mkdtemp(), delay=0, **kwargs)
        events = queue.Queue()
        job = DownloadJob(options, events)
        job.start()
        out = drain(events)
        job.join(5)
        return job, out

    def test_events_tell_the_whole_story(self):
        job, events = self.run_job(categories=ALL, depth=2)
        kinds = [k for k, _ in events]
        self.assertEqual(kinds[-1], "done")
        self.assertEqual(kinds.count("found"), 9)
        self.assertEqual(kinds.count("result"), 9)
        self.assertLess(kinds.index("found"), kinds.index("result"))
        self.assertEqual(events[-1][1]["statuses"], {"downloaded": 9})

    def test_found_files_are_numbered_in_order(self):
        _, events = self.run_job(categories=ALL, depth=1, list_only=True)
        numbers = [payload[0] for kind, payload in events if kind == "found"]
        self.assertEqual(numbers, list(range(len(numbers))))

    def test_list_only_downloads_nothing(self):
        job, events = self.run_job(categories=("documents",), list_only=True)
        self.assertEqual([k for k, _ in events].count("result"), 0)
        self.assertEqual(list(Path(job.options.folder).rglob("*.pdf")), [])

    def test_stop_before_start(self):
        options = JobOptions(url=self.server.base, folder=tempfile.mkdtemp(), delay=0, categories=ALL)
        events = queue.Queue()
        job = DownloadJob(options, events)
        job.stop()
        job.start()
        summary = drain(events)[-1][1]
        self.assertTrue(summary["stopped"])
        self.assertEqual(summary["files"], 0)

    def test_pause_and_resume(self):
        options = JobOptions(url=self.server.base, folder=tempfile.mkdtemp(), delay=0, categories=ALL)
        job = DownloadJob(options, queue.Queue())
        job.pause()
        self.assertTrue(job.paused)
        job.resume()
        self.assertFalse(job.paused)
        self.assertFalse(job.should_stop())

    def test_bad_url_reports_an_error(self):
        options = JobOptions(url="not a url", folder=tempfile.mkdtemp())
        events = queue.Queue()
        DownloadJob(options, events).start()
        summary = drain(events)[-1][1]
        self.assertIn("not a web address", summary["error"])


class TestCli(unittest.TestCase):
    def test_parser_defaults(self):
        args = build_parser().parse_args(["https://s.com"])
        options = options_from(args)
        self.assertEqual(options.depth, 1)
        self.assertTrue(options.respect_robots)
        self.assertTrue(options.subfolders)
        self.assertEqual(set(options.categories), set(ALL))

    def test_options_flags(self):
        args = build_parser().parse_args(["https://s.com", "--types", "audio", "--ignore-robots", "--flat",
                                          "--any-site", "--include", "*mix*", "--max-size", "5", "--list"])
        o = options_from(args)
        self.assertEqual((o.categories, o.respect_robots, o.subfolders, o.same_site_only, o.include,
                          o.max_size_mb, o.list_only), (("audio",), False, False, False, ("*mix*",), 5, True))

    def test_run_downloads_and_exits_zero(self):
        with TestServer() as server:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main([server.base, "--out", tempfile.mkdtemp(), "--delay", "0", "--types", "documents"])
        self.assertEqual(code, 0)
        self.assertIn("2 downloaded", out.getvalue())
        self.assertIn("1 link blocked by robots.txt", out.getvalue())

    def test_failed_download_exit_code(self):
        with TestServer() as server:
            server.fail("/flaky/docs/report.pdf", times=99)   # broken.html links here
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main([server.base + "broken.html", "--out", tempfile.mkdtemp(), "--delay", "0",
                             "--depth", "0", "--types", "documents"])
        self.assertEqual(code, 1)
        self.assertIn("1 failed", out.getvalue())


class TestAppHelpers(unittest.TestCase):
    def test_validate(self):
        self.assertEqual(validate("https://s.com", ["documents"], "C:/x"), [])
        self.assertEqual(len(validate("s.com", [], "")), 3)
