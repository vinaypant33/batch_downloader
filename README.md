# Batch Downloader

### Website scraper and batch file downloader

A desktop app (and command line tool) that crawls a website, finds every
video, audio file, image, document or archive it links to, and downloads them
into tidy folders: politely, in parallel, and able to resume where it left off.

## Features

- **Pick what you want**: videos, audio, images, documents (PDF, Office, CSV)
  and archives, plus name patterns like `*report*` and a maximum file size
- **Crawl depth 0–5**: just the page you give it, or follow its links several
  levels deep, staying on the same site
- **Polite by default**: reads `robots.txt`, honours `Crawl-delay`, waits
  between pages and identifies itself with a clear user agent
- **Fast and safe downloads**: up to 8 at once, an optional speed limit,
  automatic retries for network and server errors
- **Resumes interrupted downloads** using HTTP Range requests
- **Never overwrites**: files already downloaded are skipped; a different file
  with the same name is saved as `name (1).ext`
- **Spots duplicates**: identical files (same SHA-256) from different links are
  only kept once
- **History**: every download is recorded; view it in the app or export a CSV
- **Pause, resume and stop** at any time, and **Retry failed** with one click
- A log file per folder, and settings are remembered between runs
- Double-click a row to open the file; right-click to copy its link
- Dark and light themes

## Install

Needs Python 3.9 or newer.

```
pip install -r requirements.txt
```

This installs `requests`, `beautifulsoup4` and `customtkinter`.

## Using the app

```
python main.py
```

1. Paste the website address.
2. Tick the file types you want and set the depth.
3. Choose the folder to save into.
4. Optionally narrow it down: name patterns, maximum size, speed limit.
5. Press **Find & Download**. Files appear in the table as they are found,
   then each row shows its progress and result.

Tick **Only list files** to see what would be downloaded without downloading
anything. **History** shows everything downloaded into the chosen folder and
**Export CSV** saves that list.

Shortcuts: **Ctrl+Enter** starts, **Esc** stops, double-click opens a file.

## Using the command line

```
python -m batch_downloader https://example.com/reports --types documents --depth 2 --out reports
python -m batch_downloader https://example.com --list
python -m batch_downloader https://example.com/media --types videos --max-size 500 --speed-limit 2048
```

| Option | Meaning |
|---|---|
| `--types` | any of `archives audio documents images videos` (default: all) |
| `--depth N` | levels of links to follow (default 1) |
| `--out DIR` | download folder |
| `--include` / `--exclude` | file name patterns such as `*report*` |
| `--max-size MB` | skip bigger files |
| `--speed-limit KB/S` | cap the total download speed |
| `--workers N` | parallel downloads (default 4) |
| `--delay S` | seconds between page requests (default 0.5) |
| `--sitemap` | also crawl pages listed in `sitemap.xml` |
| `--any-site` | follow links to other websites |
| `--flat` | one folder instead of one per type |
| `--list` | list the files only |

The exit code is `0` on success, `1` if any download failed and `2` for an
error such as an invalid address.

## Where files go

```
<folder>/
  documents/   report.pdf, Annual Summary.pdf
  images/      logo.png
  videos/      clip.mp4
  audio/       song.mp3
  archives/    data.zip
  .batch_downloader.sqlite    download history
```

Partly downloaded files end in `.part` and are resumed next time.

## Using it responsibly

Only download content you are allowed to: check a site's terms of use and
copyright before saving its files. The defaults respect `robots.txt` and wait
between requests; `--ignore-robots` and a zero delay exist for your own sites
and testing.
