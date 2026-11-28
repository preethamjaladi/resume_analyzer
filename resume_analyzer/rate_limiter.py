
"""Process-local rate limits for anonymous analysis requests."""

import math
import threading
import time

from collections import deque
from contextlib import contextmanager

from fastapi import HTTPException


class AnalysisRateLimiter:
    def __init__(
        self,
        max_requests=30,
        window_seconds=3600,
        max_concurrent=2,
        clock=None,
    ):
        if min(max_requests, window_seconds, max_concurrent) <= 0:
            raise ValueError("Rate limit settings must be positive")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clock = clock or time.monotonic

        self.timestamps = deque()
        self.lock = threading.Lock()
        self.semaphore = threading.BoundedSemaphore(
            max_concurrent
        )

    def _claim_request(self):
        now = self.clock()

        with self.lock:
            # Rolling time window, rather than resetting
            # all counters at the top of each hour.
            while (
                self.timestamps
                and now - self.timestamps[0]
                >= self.window_seconds
            ):
                self.timestamps.popleft()

            if len(self.timestamps) >= self.max_requests:
                retry_after = math.ceil(
                    self.window_seconds
                    - (now - self.timestamps[0])
                )

                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Analysis limit reached. "
                        "Please try again later."
                    ),
                    headers={
                        "Retry-After": str(
                            max(1, retry_after)
                        )
                    },
                )

            # Only admitted requests consume quota.
            self.timestamps.append(now)

    @contextmanager
    def admit(self):
        # Never queue unlimited requests waiting for Groq.
        if not self.semaphore.acquire(blocking=False):
            raise HTTPException(
                status_code=503,
                detail=(
                    "All analysis slots are busy. "
                    "Please retry shortly."
                ),
                headers={"Retry-After": "5"},
            )

        try:
            self._claim_request()
            yield
        finally:
            self.semaphore.release()
