"""Respect each site's robots.txt."""

import threading
from urllib.robotparser import RobotFileParser

import requests

from .urls import robots_url


class RobotsCache:
    """Downloads robots.txt once per site and answers 'may I fetch this?'."""

    def __init__(self, session, user_agent, timeout=10):
        self.session = session
        self.user_agent = user_agent
        self.timeout = timeout
        self._parsers = {}
        self._lock = threading.Lock()

    def _parser(self, url):
        key = robots_url(url)
        with self._lock:
            if key in self._parsers:
                return self._parsers[key]
        parser = RobotFileParser()
        try:
            response = self.session.get(key, timeout=self.timeout, headers={"User-Agent": self.user_agent})
            if response.status_code >= 400:
                parser.allow_all = True       # no robots.txt: everything is allowed
            else:
                parser.parse(response.text.splitlines())
        except requests.RequestException:
            parser.allow_all = True           # unreachable: do not block the crawl
        with self._lock:
            self._parsers[key] = parser
        return parser

    def allowed(self, url):
        return self._parser(url).can_fetch(self.user_agent, url)

    def crawl_delay(self, url):
        """Seconds the site asks crawlers to wait between requests, if any."""
        delay = self._parser(url).crawl_delay(self.user_agent)
        return float(delay) if delay else None
