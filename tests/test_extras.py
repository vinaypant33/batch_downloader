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
