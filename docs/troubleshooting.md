# Troubleshooting

## Nothing is found

- Check the depth. At depth 0 only the page you entered is read; most sites
  list files one or two clicks deep.
- Make sure the right file types are ticked, and that the name patterns are
  not too narrow (`*report*` will not match `summary.pdf`).
- The site may build its links with JavaScript. The crawler reads the HTML the
  server sends and does not run scripts, so those links are invisible to it.

## "links blocked by robots.txt"

The site asked crawlers to stay out of those pages. Respect that for sites you
do not own. For your own site or a test server, untick **Respect robots.txt**
or pass `--ignore-robots`.

## Downloads fail with HTTP 403 or 429

**429 Too Many Requests** means the site is rate-limiting you. Batch Downloader
already waits (as long as the site's `Retry-After` header asks, up to a minute)
and retries four times. If files still fail, lower the parallel downloads or set
a speed limit, then press **Retry failed**.

**403 Forbidden** means the site refuses automated downloads. Respect that.

## Only small thumbnails are downloaded

The page shows thumbnails that link to a page per picture. Set the depth to at
least 1 so those pages are opened and the full-size originals are found, and
exclude the thumbnails, e.g. `--exclude "*px-*"` on Wikimedia.

## A download stopped half way

Run the same download again (or press **Retry failed**). The `.part` file is
resumed from where it stopped if the server supports Range requests; if not,
the file starts again from the beginning.

## Where is the log?

Each run writes `batch_downloader.log` in the download folder, with every page
error, retry and failure.
