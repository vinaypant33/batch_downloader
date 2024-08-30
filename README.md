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
