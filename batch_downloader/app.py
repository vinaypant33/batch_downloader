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


class App(ctk.CTk):
    def __init__(self, settings_path=None):
        super().__init__()
        self.settings_path = settings_path
        self.settings = load_settings(settings_path) if settings_path else load_settings()
        ctk.set_appearance_mode(self.settings.theme)
        ctk.set_default_color_theme("blue")
        self.title("Batch Downloader")
        self.geometry("900x660")
        self.minsize(820, 560)
        self.job = None
        self.events = queue.Queue()
        self.total_files = 0
        self.finished_files = 0
        self.rows = {}          # table row -> {"found": FoundFile, "result": DownloadResult}
        self.build()
        self.load_into_controls()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Control-Return>", lambda _e: self.start())
        self.bind("<Escape>", lambda _e: self.stop())

    def build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.build_url_row()
        self.build_options()
        self.build_folder_row()
        self.build_advanced()
        self.build_table()
        self.build_footer()

    def build_url_row(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        row.grid_columnconfigure(0, weight=1)
        self.url_entry = ctk.CTkEntry(row, placeholder_text="Website address, e.g. https://example.com/downloads")
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.url_entry.bind("<Return>", lambda _e: self.start())
        self.start_button = ctk.CTkButton(row, text="Find & Download", width=150, command=self.start)
        self.start_button.grid(row=0, column=1)

    def build_options(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, sticky="ew", padx=12, pady=6)
        self.category_vars = {}
        for column, category in enumerate(CATEGORIES):
            var = tk.BooleanVar()
            self.category_vars[category] = var
            ctk.CTkCheckBox(frame, text=LABELS[category], variable=var).grid(
                row=0, column=column, padx=8, pady=10, sticky="w")
        depth_box = ctk.CTkFrame(frame, fg_color="transparent")
        depth_box.grid(row=0, column=len(CATEGORIES), padx=8)
        self.depth_label = ctk.CTkLabel(depth_box, text="Depth: 1")
        self.depth_label.pack()
        self.depth_slider = ctk.CTkSlider(depth_box, from_=0, to=5, number_of_steps=5, width=120,
                                          command=lambda v: self.depth_label.configure(text=f"Depth: {round(v)}"))
        self.depth_slider.pack()
