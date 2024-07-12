"""
A local web server for the tests, serving tests/site/.

On top of plain files it supports what real servers do and the tests need:
  * HTTP Range requests (206 / 416), for resuming downloads
  * /flaky/<name>  fails with 503 a set number of times, then works
  * /slow/<name>   sends the file in small, slow pieces
  * request counting, to check politeness and retries
No internet access is needed.
"""

import functools
import os
import threading
import time
from collections import Counter
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SITE = Path(__file__).resolve().parent / "site"
