"""Batch Downloader: find and download files from a website."""

import logging

__version__ = "1.1.0"

# Libraries stay quiet unless the app sets up logging (see log.py).
logging.getLogger(__name__).addHandler(logging.NullHandler())
