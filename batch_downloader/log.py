"""A log file in the download folder, for finding out what happened later."""

import logging
from pathlib import Path

LOG_NAME = "batch_downloader.log"
FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
