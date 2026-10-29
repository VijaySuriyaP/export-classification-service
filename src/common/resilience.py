"""Bounded retry and simple circuit-breaker primitives."""
from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class CircuitBreaker:
    """Minimal process-local closed/open/half-open breaker for provider calls."""

    def __init__(self, threshold: int = 3, reset_s: int = 30) -> None:
        self.threshold = threshold
        self.reset_s = reset_s
        self.failures = 0
        self.opened_at: float | None = None

    @property
    def state(self) -> str:
        if self.opened_at is None:
            return "closed"
        return "half-open" if time.monotonic() - self.opened_at >= self.reset_s else "open"

    def call(self, fn: Callable[[], T]) -> T:
        """Run one callable unless the breaker is open; update state on outcome."""
        if self.state == "open":
            raise RuntimeError("provider circuit breaker is open")
        try:
            result = fn()
        except Exception:
            self.failures += 1
            if self.failures >= self.threshold:
                self.opened_at = time.monotonic()
            raise
        self.failures = 0
        self.opened_at = None
        return result


def retry_call(fn: Callable[[], T], attempts: int = 2, base_delay_s: float = 0.05) -> T:
    """Retry a callable a bounded number of times with jittered backoff."""
    for attempt in range(attempts):
        try:
            return fn()
        except Exception:
            if attempt + 1 >= attempts:
                raise
            time.sleep(base_delay_s * (2**attempt) * (0.5 + random.random()))
    raise RuntimeError("unreachable retry state")
