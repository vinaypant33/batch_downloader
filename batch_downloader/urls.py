"""URL clean-up and site checks used by the crawler."""

from urllib.parse import parse_qsl, urldefrag, urlencode, urljoin, urlparse, urlunparse

PAGE_EXTENSIONS = ("", ".html", ".htm", ".php", ".asp", ".aspx", ".jsp", ".shtml")
DEFAULT_PORTS = {"http": 80, "https": 443}
TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid")


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
    return urlunparse((scheme, netloc, path, parts.params, strip_tracking(parts.query), ""))


def strip_tracking(query):
    """Drop tracking parameters (utm_source, fbclid, ...) so one file has one address."""
    if not query:
        return query
    kept = [(k, v) for k, v in parse_qsl(query, keep_blank_values=True)
            if not k.lower().startswith(TRACKING_PREFIXES)]
    return urlencode(kept)


def host_of(url):
    """Host without 'www.' and with the port, used to compare sites."""
    parts = urlparse(url)
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return f"{host}:{parts.port}" if parts.port else host


def same_site(a, b):
    return host_of(a) == host_of(b)


def looks_like_page(url):
    """True when a URL probably points at an HTML page rather than a file."""
    path = urlparse(url).path.lower()
    last = path.rsplit("/", 1)[-1]
    if "." not in last:
        return True
    return "." + last.rsplit(".", 1)[-1] in PAGE_EXTENSIONS


def robots_url(url):
    parts = urlparse(url)
    return urlunparse((parts.scheme, parts.netloc, "/robots.txt", "", "", ""))
