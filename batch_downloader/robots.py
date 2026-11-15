"""Respect each site's robots.txt."""

import threading
import time
from urllib.robotparser import RobotFileParser

import requests

from .urls import robots_url


class RobotsCache:
    """Downloads robots.txt once per site and answers 'may I fetch this?'."""

    def __init__(self, session, user_agent, timeout=10, attempts=3):
        self.session = session
        self.user_agent = user_agent
        self.timeout = timeout
        self.attempts = max(1, attempts)
        self._parsers = {}
        self._lock = threading.Lock()

    def _parser(self, url):
        key = robots_url(url)
        with self._lock:
            if key in self._parsers:
                return self._parsers[key]
        parser = RobotFileParser()
        response = None
        for attempt in range(self.attempts):  # one network blip must not switch the rules off
            try:
                response = self.session.get(key, timeout=self.timeout, headers={"User-Agent": self.user_agent})
                break
            except requests.RequestException:
                if attempt + 1 < self.attempts:
                    time.sleep(0.5 * (attempt + 1))
        if response is None:
            parser.allow_all = True           # unreachable: do not block the crawl
        elif response.status_code >= 400:
            parser.allow_all = True           # no robots.txt: everything is allowed
        else:
            parser.parse(response.text.splitlines())
        with self._lock:
            self._parsers[key] = parser
        return parser

    def allowed(self, url):
        return self._parser(url).can_fetch(self.user_agent, url)

    def crawl_delay(self, url):
        """Seconds the site asks crawlers to wait between requests, if any."""
        delay = self._parser(url).crawl_delay(self.user_agent)
        return float(delay) if delay else None
