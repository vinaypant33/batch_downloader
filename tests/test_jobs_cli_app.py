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
