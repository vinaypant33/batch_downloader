"""
Command line version, for scripts and servers without a screen.

    python -m batch_downloader https://example.com/files --types documents images --depth 2
    python -m batch_downloader https://example.com --list
"""

import argparse
import queue
from collections import Counter

from . import __version__
from .filetypes import CATEGORIES
from .jobs import DownloadJob, JobOptions
from .settings import DEFAULT_FOLDER
from .utils import human_size, shorten


def build_parser():
    p = argparse.ArgumentParser(prog="python -m batch_downloader",
                                description="Find and download files linked from a website.")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("url", help="page to start from")
    p.add_argument("--types", nargs="+", choices=sorted(CATEGORIES), default=sorted(CATEGORIES),
                   metavar="TYPE", help=f"file types to get: {', '.join(sorted(CATEGORIES))} (default: all)")
    p.add_argument("--depth", type=int, default=1, help="how many levels of links to follow (default 1)")
    p.add_argument("--out", default=DEFAULT_FOLDER, help=f"download folder (default {DEFAULT_FOLDER})")
    p.add_argument("--include", nargs="*", default=[], metavar="PATTERN", help="only names matching, e.g. '*report*'")
    p.add_argument("--exclude", nargs="*", default=[], metavar="PATTERN", help="skip names matching, e.g. '*thumb*'")
    p.add_argument("--max-size", type=int, default=0, metavar="MB", help="skip files bigger than this")
    p.add_argument("--speed-limit", type=int, default=0, metavar="KB/S", help="limit the download speed")
    p.add_argument("--workers", type=int, default=4, help="parallel downloads (default 4)")
    p.add_argument("--delay", type=float, default=0.5, help="seconds between page requests (default 0.5)")
    p.add_argument("--sitemap", action="store_true", help="also crawl pages listed in sitemap.xml")
    p.add_argument("--any-site", action="store_true", help="follow links to other websites too")
    p.add_argument("--ignore-robots", action="store_true", help="do not check robots.txt (use with care)")
    p.add_argument("--flat", action="store_true", help="save everything in one folder, not per type")
    p.add_argument("--list", action="store_true", help="only list the files that would be downloaded")
    return p
