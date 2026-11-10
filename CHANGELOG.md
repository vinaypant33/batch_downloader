# Changelog

## 1.1.0

Fixes found by testing on real websites (Wikimedia Commons):

- Send the BatchDownloader user agent; the default `python-requests` one was
  blocked with 403 by many sites
- Download images and videos hosted on media servers / CDNs by default
- Follow links that end in `.jpg` but are web pages, to reach the full-size file;
  never save a web page under a file name
- Retry *429 Too Many Requests*, honouring `Retry-After`; 4 retries by default
- Remove tracking parameters (`utm_…`, `fbclid`) so one file has one address
- Two links that save to the same file name no longer collide
- Clear message when the start page cannot be loaded
- The command line no longer crashes on file names a Windows console cannot show

## 1.0.0

- Command line tool with every option of the app, and meaningful exit codes
- Download history window and CSV export
- Settings are remembered between runs
- Retry failed downloads, log file per folder, right-click menu and shortcuts
- GitHub Actions runs the tests on Windows and Linux

## 0.4.0

- Pause, resume and stop
- Dark and light themes for the window and the results table
- "Only list files" mode

## 0.3.0

- Resumable downloads with HTTP Range requests
- Retries with backoff for network and server errors
- Shared speed limit
- Duplicate files detected by SHA-256

## 0.2.0

- Working crawler: depth, same-site, robots.txt, Crawl-delay and sitemap.xml
- File type, name pattern and size filters
- Parallel downloads into one folder per file type

## 0.1.0 (April 2024)

- First user interface experiments with ttkbootstrap and CustomTkinter
