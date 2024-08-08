"""A log file in the download folder, for finding out what happened later."""

import logging
from pathlib import Path

LOG_NAME = "batch_downloader.log"
FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def setup_logging(folder, level=logging.INFO):
    """Send the package's log to <folder>/batch_downloader.log. Safe to call twice."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = (folder / LOG_NAME).resolve()
    logger = logging.getLogger("batch_downloader")
    logger.setLevel(level)
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == path:
            return path
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(handler)
    return path


def close_logging(folder):
    """Detach and close the handler for a folder (so the file can be moved or deleted)."""
    path = (Path(folder) / LOG_NAME).resolve()
    logger = logging.getLogger("batch_downloader")
    for handler in list(logger.handlers):
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == path:
            logger.removeHandler(handler)
            handler.close()
