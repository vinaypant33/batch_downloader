"""
The desktop window (CustomTkinter).

All slow work happens in a DownloadJob thread. The window only reads the job's
event queue every 100 ms and updates the table, so it never freezes.
"""

import os
import queue
import subprocess
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from .downloader import safe_filename
from . import __version__
from .filetypes import CATEGORIES, LABELS
from .jobs import DownloadJob, JobOptions
from .manifest import Manifest
from .settings import Settings, load_settings, save_settings
from .urls import normalize
from .utils import human_size, shorten

POLL_MS = 100


def validate(url, categories, folder):
    """Problems with the user's input, as a list of messages (empty when fine)."""
    problems = []
    if not normalize(url or ""):
        problems.append("Enter a website address starting with http:// or https://")
    if not categories:
        problems.append("Tick at least one file type")
    if not folder:
        problems.append("Choose a folder to save the files in")
    return problems


def open_folder(path):
    """Open a folder in Explorer / Finder / the file manager."""
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa: S606 - opening the user's own folder
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)
