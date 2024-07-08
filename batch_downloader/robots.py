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
