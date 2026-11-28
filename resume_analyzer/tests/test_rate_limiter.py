
"""Tests for anonymous analysis rate limiting."""

import threading

import pytest
from fastapi import HTTPException

from resume_analyzer.rate_limiter import (
    AnalysisRateLimiter,
)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_requests_within_limit():
    clock = FakeClock()

    limiter = AnalysisRateLimiter(
        max_requests=3,
        window_seconds=60,
        clock=clock,
    )

    for _ in range(3):
        with limiter.admit():
            pass

    assert len(limiter.timestamps) == 3


def test_excessive_requests_rejected():
    clock = FakeClock()

    limiter = AnalysisRateLimiter(
        max_requests=2,
        window_seconds=60,
        clock=clock,
    )

    with limiter.admit():
        pass

    with limiter.admit():
        pass

    with pytest.raises(HTTPException) as exc:
        with limiter.admit():
            pass

    assert exc.value.status_code == 429
    assert exc.value.headers["Retry-After"] == "60"


def test_limit_resets_after_window():
    clock = FakeClock()

    limiter = AnalysisRateLimiter(
        max_requests=1,
        window_seconds=60,
        clock=clock,
    )

    with limiter.admit():
        pass

    clock.advance(60)

    with limiter.admit():
        pass

    assert len(limiter.timestamps) == 1


def test_concurrent_limit():
    limiter = AnalysisRateLimiter(
        max_requests=10,
        max_concurrent=1,
    )

    entered = threading.Event()
    release = threading.Event()
    errors = []

    def first_request():
        try:
            with limiter.admit():
                entered.set()
                release.wait(timeout=5)
        except Exception as error:
            errors.append(error)

    worker = threading.Thread(target=first_request)
    worker.start()

    try:
        assert entered.wait(timeout=2)

        with pytest.raises(HTTPException) as exc:
            with limiter.admit():
                pass

        assert exc.value.status_code == 503
        assert len(limiter.timestamps) == 1

    finally:
        release.set()
        worker.join(timeout=5)

    assert not worker.is_alive()
    assert errors == []

    # Capacity is released after the first request.
    with limiter.admit():
        pass


def test_failed_admission_releases_slot():
    limiter = AnalysisRateLimiter(
        max_requests=1,
        max_concurrent=1,
    )

    with limiter.admit():
        pass

    with pytest.raises(HTTPException) as exc:
        with limiter.admit():
            pass

    assert exc.value.status_code == 429

    # The semaphore must not remain locked.
    assert limiter.semaphore.acquire(blocking=False)
    limiter.semaphore.release()
