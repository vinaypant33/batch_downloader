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
