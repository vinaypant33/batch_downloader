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
