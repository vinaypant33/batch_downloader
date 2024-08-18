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

    def build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew", padx=12, pady=(6, 12))
        footer.grid_columnconfigure(0, weight=1)
        self.progress = ctk.CTkProgressBar(footer)
        self.progress.set(0)
        self.progress.grid(row=0, column=0, columnspan=6, sticky="ew", pady=(0, 6))
        self.status_label = ctk.CTkLabel(footer, text="Ready", anchor="w")
        self.status_label.grid(row=1, column=0, sticky="ew")
        self.totals_label = ctk.CTkLabel(footer, text="", anchor="w", text_color=("gray35", "gray65"))
        self.totals_label.grid(row=2, column=0, sticky="ew")
        self.pause_button = ctk.CTkButton(footer, text="Pause", width=80, state="disabled", command=self.toggle_pause)
        self.stop_button = ctk.CTkButton(footer, text="Stop", width=80, state="disabled",
                                         fg_color="#b33a3a", hover_color="#8f2e2e", command=self.stop)
        self.pause_button.grid(row=1, column=1, padx=4)
        self.stop_button.grid(row=1, column=2, padx=4)
        self.retry_button = ctk.CTkButton(footer, text="Retry failed", width=100, state="disabled",
                                          command=self.retry_failed)
        self.retry_button.grid(row=2, column=1, columnspan=2, padx=4, pady=(4, 0))
        ctk.CTkButton(footer, text="History", width=80, command=self.show_history).grid(row=1, column=3, padx=4)
        ctk.CTkButton(footer, text="Export CSV", width=90, command=self.export_csv).grid(row=1, column=4, padx=4)
        self.theme_switch = ctk.CTkSegmentedButton(footer, values=["dark", "light"], command=self.set_theme)
        self.theme_switch.grid(row=1, column=5, padx=(4, 0))
        ctk.CTkButton(footer, text="About", width=70, command=self.show_about).grid(row=2, column=5, pady=(4, 0))

    def load_into_controls(self):
        s = self.settings
        if s.last_url:
            self.url_entry.insert(0, s.last_url)
        self.folder_entry.insert(0, s.folder)
        for category, var in self.category_vars.items():
            var.set(category in s.categories)
        self.depth_slider.set(s.depth)
        self.depth_label.configure(text=f"Depth: {s.depth}")
        for entry, value in [(self.include_entry, s.include), (self.exclude_entry, s.exclude)]:
            if value:
                entry.insert(0, value)
        if s.max_size_mb:
            self.max_size_entry.insert(0, str(s.max_size_mb))
        if s.speed_limit_kb:
            self.speed_entry.insert(0, str(s.speed_limit_kb))
        self.robots_var.set(s.respect_robots)
        self.same_site_var.set(s.same_site_only)
        self.sitemap_var.set(s.use_sitemap)
        self.theme_switch.set(s.theme if s.theme in ("dark", "light") else "dark")

    def read_controls(self):
        def number(entry):
            text = entry.get().strip()
            return int(text) if text.isdigit() else 0

        s = Settings(
            last_url=self.url_entry.get().strip(),
            folder=self.folder_entry.get().strip(),
            categories=[c for c, var in self.category_vars.items() if var.get()],
            depth=round(self.depth_slider.get()),
            delay=self.settings.delay,
            workers=self.settings.workers,
            speed_limit_kb=number(self.speed_entry),
            respect_robots=self.robots_var.get(),
            same_site_only=self.same_site_var.get(),
            use_sitemap=self.sitemap_var.get(),
            include=self.include_entry.get().strip(),
            exclude=self.exclude_entry.get().strip(),
            max_size_mb=number(self.max_size_entry),
            theme=self.theme_switch.get() or "dark",
        )
        return s

    def save(self):
        try:
            if self.settings_path:
                save_settings(self.settings, self.settings_path)
            else:
                save_settings(self.settings)
        except OSError:
            pass  # settings are a convenience; never block the user over them

    def start(self, files=()):
        if self.job and self.job.is_alive():
            return
        s = self.read_controls()
        problems = validate(s.last_url, s.categories, s.folder)
        if problems:
            messagebox.showwarning("Batch Downloader", "\n".join(problems), parent=self)
            return
        self.settings = s.clean()
        self.save()
        self.table.delete(*self.table.get_children())
        self.rows = {}
        self.total_files = self.finished_files = 0
        self.progress.set(0)
        self.totals_label.configure(text="")
        options = JobOptions(
            url=s.last_url, folder=s.folder, categories=tuple(s.categories), depth=s.depth, delay=s.delay,
            workers=s.workers, speed_limit_kb=s.speed_limit_kb, respect_robots=s.respect_robots,
            same_site_only=s.same_site_only, use_sitemap=s.use_sitemap, subfolders=s.subfolders,
            include=Settings.patterns(s.include), exclude=Settings.patterns(s.exclude),
            max_size_mb=s.max_size_mb, list_only=self.list_only_var.get(), files=tuple(files),
        )
        self.events = queue.Queue()
        self.job = DownloadJob(options, self.events)
        self.job.start()
        self.set_running(True)
        self.after(POLL_MS, self.poll)

    def set_running(self, running):
        self.start_button.configure(state="disabled" if running else "normal")
        self.pause_button.configure(state="normal" if running else "disabled", text="Pause")
        self.stop_button.configure(state="normal" if running else "disabled")
        self.retry_button.configure(state="disabled")

    def poll(self):
        """Apply every event the job has sent since the last poll."""
        finished = False
        try:
            while True:
                kind, payload = self.events.get_nowait()
                finished = self.handle(kind, payload) or finished
        except queue.Empty:
            pass
        if not finished:
            self.after(POLL_MS, self.poll)

    def handle(self, kind, payload):
        if kind == "status":
            self.status_label.configure(text=payload)
        elif kind == "page":
            url, depth = payload
            self.status_label.configure(text=f"Crawling (depth {depth}): {shorten(url, 80)}")
        elif kind == "found":
            index, found = payload
            self.total_files = index + 1
            name = safe_filename(found.url)
            self.table.insert("", "end", iid=str(index),
                              values=(index + 1, shorten(name, 70), found.category, "", "found"))
            self.rows[str(index)] = {"found": found, "result": None}
        elif kind == "progress":
            index, done, total = payload
            percent = f"{done * 100 // total}%" if total else human_size(done)
            self.table.set(str(index), "status", f"downloading {percent}")
        elif kind == "result":
            index, result = payload
            self.finished_files += 1
            self.table.set(str(index), "size", human_size(result.size) if result.size else "")
            self.table.set(str(index), "status", result.status if not result.error else f"{result.status}: {result.error}")
            self.rows[str(index)]["result"] = result
            if self.total_files:
                self.progress.set(self.finished_files / self.total_files)
                self.title(f"Batch Downloader - {self.finished_files * 100 // self.total_files}%")
            self.update_totals()
        elif kind == "done":
            self.on_done(payload)
            return True
        return False

    def on_done(self, summary):
        self.set_running(False)
        self.title("Batch Downloader")
        if self.failed_files():
            self.retry_button.configure(state="normal")
        if summary.get("error"):
            self.status_label.configure(text=f"Error: {summary['error']}")
            return
        counts = ", ".join(f"{n} {status}" for status, n in sorted(summary.get("statuses", {}).items()))
        word = "Stopped" if summary.get("stopped") else "Done"
        self.status_label.configure(
            text=f"{word}: {summary['files']} files found on {summary['pages']} pages" + (f" ({counts})" if counts else ""))
        if not summary.get("stopped"):
            self.progress.set(1)

    def toggle_pause(self):
        if not self.job:
            return
        if self.job.paused:
            self.job.resume()
            self.pause_button.configure(text="Pause")
        else:
            self.job.pause()
            self.pause_button.configure(text="Resume")

    def stop(self):
        if self.job:
            self.job.stop()
            self.status_label.configure(text="Stopping…")

    def choose_folder(self):
        folder = filedialog.askdirectory(parent=self, initialdir=self.folder_entry.get() or str(Path.home()))
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)

    def open_download_folder(self):
        folder = self.folder_entry.get().strip()
        if folder and Path(folder).is_dir():
            open_folder(folder)
        else:
            messagebox.showinfo("Batch Downloader", "The folder does not exist yet.", parent=self)

    def show_history(self):
        folder = self.folder_entry.get().strip()
        if not folder or not Path(folder).is_dir():
            messagebox.showinfo("Batch Downloader", "No downloads in this folder yet.", parent=self)
            return
        manifest = Manifest(folder)
        rows = manifest.history()
        manifest.close()
        window = ctk.CTkToplevel(self)
        window.title("Download history")
        window.geometry("860x420")
        table = ttk.Treeview(window, columns=("when", "status", "type", "size", "file"),
                             show="headings", style="Files.Treeview")
        for column, title, width in [("when", "When", 150), ("status", "Status", 100), ("type", "Type", 100),
                                     ("size", "Size", 90), ("file", "File", 380)]:
            table.heading(column, text=title)
            table.column(column, width=width, stretch=column == "file")
        for row in rows:
            table.insert("", "end", values=(row["finished_at"], row["status"], row["category"] or "",
                                            human_size(row["size"]), row["path"] or row["url"]))
        table.pack(fill="both", expand=True, padx=10, pady=10)
        window.after(100, window.lift)

    def export_csv(self):
        folder = self.folder_entry.get().strip()
        if not folder or not Path(folder).is_dir():
            messagebox.showinfo("Batch Downloader", "No downloads in this folder yet.", parent=self)
            return
        target = filedialog.asksaveasfilename(parent=self, defaultextension=".csv",
                                              initialfile="downloads.csv", filetypes=[("CSV", "*.csv")])
        if target:
            manifest = Manifest(folder)
            count = manifest.export_csv(target)
            manifest.close()
            self.status_label.configure(text=f"Exported {count} rows to {target}")

    def set_theme(self, theme):
        ctk.set_appearance_mode(theme)
        self.style_table()
        self.settings.theme = theme
        self.save()

    def on_close(self):
        if self.job and self.job.is_alive():
            if not messagebox.askyesno("Batch Downloader", "A download is running. Stop it and quit?", parent=self):
                return
            self.job.stop()
        self.settings = self.read_controls().clean()
        self.save()
        self.destroy()


    def update_totals(self):
        results = [r["result"] for r in self.rows.values() if r["result"]]
        done = sum(r.status == "downloaded" for r in results)
        failed = sum(r.status == "failed" for r in results)
        size = sum(r.size for r in results if r.status == "downloaded")
        self.totals_label.configure(
            text=f"{len(self.rows)} found · {done} downloaded ({human_size(size)}) · {failed} failed")

    def failed_files(self):
        return [r["found"] for r in self.rows.values() if r["result"] and r["result"].status == "failed"]

    def retry_failed(self):
        files = self.failed_files()
        if files:
            self.start(files=files)

    def selected_row(self):
        selection = self.table.selection()
        return self.rows.get(selection[0]) if selection else None

    def open_selected_file(self, _event=None):
        row = self.selected_row()
        result = row and row["result"]
        if result and result.path and Path(result.path).exists():
            open_folder(result.path)

    def show_row_menu(self, event):
        iid = self.table.identify_row(event.y)
        if not iid:
            return
        self.table.selection_set(iid)
        row = self.rows[iid]
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Open file", command=self.open_selected_file,
                         state="normal" if row["result"] and row["result"].path else "disabled")
        menu.add_command(label="Copy link", command=lambda: self.copy_text(row["found"].url))
        menu.add_command(label="Open page in browser", command=lambda: webbrowser.open(row["found"].page))
        menu.tk_popup(event.x_root, event.y_root)

    def copy_text(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_label.configure(text="Link copied")

    def show_about(self):
        messagebox.showinfo("Batch Downloader",
                            f"Batch Downloader {__version__}\n\nFinds and downloads files linked from a website.\n"
                            "Shortcuts: Ctrl+Enter start, Esc stop, double-click opens a file.", parent=self)
