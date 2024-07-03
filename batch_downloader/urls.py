"""URL clean-up and site checks used by the crawler."""

from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

PAGE_EXTENSIONS = ("", ".html", ".htm", ".php", ".asp", ".aspx", ".jsp", ".shtml")
DEFAULT_PORTS = {"http": 80, "https": 443}


def normalize(url, base=None):
    """Make a link absolute and tidy. Returns None for non-web links.

    'docs/a.pdf#top' on https://Site.com/x/ -> 'https://site.com/x/docs/a.pdf'
    """
    if not url:
        return None
    url = url.strip()
    if base:
        url = urljoin(base, url)
    url, _fragment = urldefrag(url)
    parts = urlparse(url)
    if parts.scheme.lower() not in DEFAULT_PORTS or not parts.netloc:
        return None  # mailto:, javascript:, data:, ftp: ...
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    netloc = host
    if parts.port and parts.port != DEFAULT_PORTS[scheme]:
        netloc = f"{host}:{parts.port}"
    path = parts.path or "/"
    return urlunparse((scheme, netloc, path, parts.params, parts.query, ""))
