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
