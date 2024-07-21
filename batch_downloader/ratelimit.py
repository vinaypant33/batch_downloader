"""A shared download speed limit."""

import threading
import time


class TokenBucket:
    """Allows `rate` bytes per second on average, shared by every download thread."""

    def __init__(self, rate, burst=None, clock=time.monotonic, sleep=time.sleep):
        if rate <= 0:
            raise ValueError("rate must be positive")
        self.rate = float(rate)
        self.capacity = float(burst or rate)
        self.tokens = self.capacity
        self.clock = clock
        self.sleep = sleep
        self.updated = clock()
        self._lock = threading.Lock()

    def consume(self, amount):
        """Block until `amount` bytes may be sent. Returns seconds waited."""
        with self._lock:
            now = self.clock()
            self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
            self.updated = now
            self.tokens -= amount
            wait = -self.tokens / self.rate if self.tokens < 0 else 0.0
        if wait:
            self.sleep(wait)
        return wait
