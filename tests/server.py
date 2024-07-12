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


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.requests[self.path.split("?")[0]] += 1
        if self.path.startswith("/flaky/"):
            key = self.path
            if self.server.failures.get(key, 0) > 0:
                self.server.failures[key] -= 1
                self.send_error(503, "try again")
                return
            self.path = "/" + self.path[len("/flaky/"):]
        if self.path.startswith("/slow/"):
            self.path = "/" + self.path[len("/slow/"):]
            return self.send_file(slow=True)
        return self.send_file()
