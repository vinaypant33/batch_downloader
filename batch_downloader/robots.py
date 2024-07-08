"""Respect each site's robots.txt."""

import threading
from urllib.robotparser import RobotFileParser

import requests

from .urls import robots_url
