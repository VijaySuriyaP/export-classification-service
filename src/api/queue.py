"""Redis list queue abstraction with an isolated in-memory test fallback."""
from __future__ import annotations

import os
import threading
from collections import deque

QUEUE_NAME = "export:runs"
_memory_queue: deque[str] = deque()
_lock = threading.Lock()


def _client():
    try:
        import redis

        return redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    except ImportError:
        return None


def enqueue(run_id: str) -> None:
    """Queue a run ID; memory fallback exists for unit tests without Redis."""
    client = _client()
    if client is None:
        if os.getenv("REDIS_REQUIRED", "false").lower() == "true":
            raise RuntimeError("Redis client package is required")
        with _lock:
            _memory_queue.append(run_id)
        return
    try:
        client.rpush(QUEUE_NAME, run_id)
    except Exception:
        if os.getenv("REDIS_REQUIRED", "false").lower() == "true":
            raise
        with _lock:
            _memory_queue.append(run_id)


def queue_length() -> int:
    """Return queue length for health/demo/testing purposes."""
    client = _client()
    if client is not None:
        try:
            return int(client.llen(QUEUE_NAME))
        except Exception:
            pass
    with _lock:
        return len(_memory_queue)


def pop_memory() -> str | None:
    """Pop one in-memory test queue item."""
    with _lock:
        return _memory_queue.popleft() if _memory_queue else None


def reset_memory_queue() -> None:
    """Empty the in-memory fallback between tests."""
    with _lock:
        _memory_queue.clear()
