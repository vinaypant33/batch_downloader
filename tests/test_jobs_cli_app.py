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
