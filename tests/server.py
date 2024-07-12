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

    def send_file(self, slow=False):
        path = Path(self.translate_path(self.path))
        if path.is_dir():
            index = path / "index.html"
            if not index.exists():
                return super().do_GET()
            path = index
        if not path.exists():
            self.send_error(404, "not found")
            return
        data = path.read_bytes()
        start = 0
        header = self.headers.get("Range", "")
        if header.startswith("bytes=") and self.server.ranges:
            start = int(header[6:].split("-")[0] or 0)
            if start >= len(data):
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{len(data)}")
                self.end_headers()
                return
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(data) - 1}/{len(data)}")
        else:
            self.send_response(200)
        body = data[start:]
        self.send_header("Content-Type", self.guess_type(str(path)))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            if slow:
                for i in range(0, len(body), 256):
                    self.wfile.write(body[i:i + 256])
                    self.wfile.flush()
                    time.sleep(0.01)
            else:
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # the client stopped reading (e.g. the Stop test)


class TestServer:
    def __init__(self, ranges=True):
        handler = functools.partial(Handler, directory=os.fspath(SITE))
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.httpd.daemon_threads = True
        self.httpd.requests = Counter()
        self.httpd.failures = {}
        self.httpd.ranges = ranges
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    @property
    def base(self):
        return f"http://127.0.0.1:{self.httpd.server_port}/"

    @property
    def requests(self):
        return self.httpd.requests

    def fail(self, path, times):
        self.httpd.failures[path] = times

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()
