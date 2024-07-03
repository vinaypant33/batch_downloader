"""URL clean-up and site checks used by the crawler."""

from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

PAGE_EXTENSIONS = ("", ".html", ".htm", ".php", ".asp", ".aspx", ".jsp", ".shtml")
DEFAULT_PORTS = {"http": 80, "https": 443}
