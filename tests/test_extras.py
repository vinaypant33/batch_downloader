import contextlib
import io
import logging
import queue
import tempfile
import unittest
from pathlib import Path

from batch_downloader import __version__
from batch_downloader.cli import main
from batch_downloader.crawler import FoundFile
from batch_downloader.jobs import DownloadJob, JobOptions
from batch_downloader.log import LOG_NAME, close_logging, setup_logging
from tests.server import TestServer
from tests.test_jobs_cli_app import display_available, drain


class TestLogging(unittest.TestCase):
    def test_log_file_is_written(self):
        folder = Path(tempfile.mkdtemp())
        path = setup_logging(folder)
        logging.getLogger("batch_downloader.test").info("hello log")
        close_logging(folder)
        self.assertEqual(path.name, LOG_NAME)
        self.assertIn("hello log", path.read_text(encoding="utf-8"))

    def test_setup_twice_adds_one_handler(self):
        folder = Path(tempfile.mkdtemp())
        setup_logging(folder)
        setup_logging(folder)
        handlers = [h for h in logging.getLogger("batch_downloader").handlers
                    if isinstance(h, logging.FileHandler) and Path(h.baseFilename).parent == folder.resolve()]
        self.assertEqual(len(handlers), 1)
        close_logging(folder)

    def test_job_writes_a_log(self):
        with TestServer() as server:
            options = JobOptions(url=server.base, folder=tempfile.mkdtemp(), delay=0, categories=("documents",))
            events = queue.Queue()
            DownloadJob(options, events).start()
            drain(events)
        text = (Path(options.folder) / LOG_NAME).read_text(encoding="utf-8")
        self.assertIn("job started", text)
        self.assertIn("job finished", text)


class TestRetryGivenFiles(unittest.TestCase):
    def test_given_files_skip_the_crawl(self):
        with TestServer() as server:
            files = (FoundFile(server.base + "docs/deep.pdf", "documents", server.base, 0),)
            options = JobOptions(url=server.base, folder=tempfile.mkdtemp(), delay=0, files=files)
            events = queue.Queue()
            DownloadJob(options, events).start()
            out = drain(events)
            self.assertEqual(server.requests["/"], 0)          # start page never fetched
        kinds = [k for k, _ in out]
        self.assertEqual(kinds.count("found"), 1)
        self.assertEqual(out[-1][1]["statuses"], {"downloaded": 1})


class TestVersion(unittest.TestCase):
    def test_version_flag(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
            main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn(__version__, out.getvalue())
