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

    def build_folder_row(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=2, column=0, sticky="ew", padx=12, pady=6)
        row.grid_columnconfigure(0, weight=1)
        self.folder_entry = ctk.CTkEntry(row, placeholder_text="Folder to save files in")
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(row, text="Choose…", width=90, command=self.choose_folder).grid(row=0, column=1, padx=(0, 8))
        ctk.CTkButton(row, text="Open folder", width=100, command=self.open_download_folder).grid(row=0, column=2)

    def build_advanced(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=3, column=0, sticky="ew", padx=12, pady=6)
        self.include_entry = self._labelled_entry(frame, "Only names like", "*report*, *2024*", 0)
        self.exclude_entry = self._labelled_entry(frame, "Skip names like", "*thumb*", 2)
        self.max_size_entry = self._labelled_entry(frame, "Max size (MB)", "0 = no limit", 4, width=110)
        self.speed_entry = self._labelled_entry(frame, "Speed limit (KB/s)", "0 = unlimited", 6, width=110)
        self.robots_var = tk.BooleanVar(value=True)
        self.same_site_var = tk.BooleanVar(value=True)
        self.sitemap_var = tk.BooleanVar(value=False)
        self.list_only_var = tk.BooleanVar(value=False)
        for column, (text, var) in enumerate([
            ("Respect robots.txt", self.robots_var), ("Stay on this site", self.same_site_var),
            ("Use sitemap.xml", self.sitemap_var), ("Only list files", self.list_only_var),
        ]):
            ctk.CTkCheckBox(frame, text=text, variable=var).grid(
                row=1, column=column * 2, columnspan=2, padx=8, pady=(0, 10), sticky="w")

    def _labelled_entry(self, frame, label, placeholder, column, width=160):
        ctk.CTkLabel(frame, text=label).grid(row=0, column=column, padx=(8, 4), pady=10, sticky="e")
        entry = ctk.CTkEntry(frame, placeholder_text=placeholder, width=width)
        entry.grid(row=0, column=column + 1, padx=(0, 8), pady=10, sticky="w")
        return entry

    def build_table(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=4, column=0, sticky="nsew", padx=12, pady=6)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.style_table()
        columns = ("no", "file", "type", "size", "status")
        self.table = ttk.Treeview(frame, columns=columns, show="headings", style="Files.Treeview")
        for column, title, width, anchor in [
            ("no", "#", 50, "e"), ("file", "File", 420, "w"), ("type", "Type", 110, "w"),
            ("size", "Size", 100, "e"), ("status", "Status", 140, "w"),
        ]:
            self.table.heading(column, text=title)
            self.table.column(column, width=width, anchor=anchor, stretch=column == "file")
        scroll = ctk.CTkScrollbar(frame, command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=6)
        scroll.grid(row=0, column=1, sticky="ns", pady=6)
        self.table.bind("<Double-1>", self.open_selected_file)
        self.table.bind("<Button-3>", self.show_row_menu)

    def style_table(self):
        dark = ctk.get_appearance_mode() == "Dark"
        background, foreground, header = ("#1f2328", "#e6e6e6", "#2b3138") if dark else ("#ffffff", "#1d1d1f", "#eef1f4")
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Files.Treeview", background=background, fieldbackground=background,
                        foreground=foreground, rowheight=26, borderwidth=0)
        style.configure("Files.Treeview.Heading", background=header, foreground=foreground, relief="flat")
        style.map("Files.Treeview", background=[("selected", "#1f6aa5")], foreground=[("selected", "white")])
