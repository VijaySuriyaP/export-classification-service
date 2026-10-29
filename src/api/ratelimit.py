"""Per-client fixed-window Redis rate limiter with process-local fallback."""
from __future__ import annotations

import os
import time
from collections import defaultdict

_counts: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))


def allow_request(client_id: str, limit: int | None = None) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds) using a 60-second fixed window."""
    limit = limit or int(os.getenv("RATE_LIMIT_PER_MIN", "60"))
    now = int(time.time())
    window = now // 60
    try:
        import redis

        client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        key = f"export:rate:{client_id}:{window}"
        count = client.incr(key)
        if count == 1:
            client.expire(key, 70)
        return count <= limit, 60 - (now % 60)
    except Exception:
        previous_window, count = _counts[client_id]
        count = count + 1 if previous_window == window else 1
        _counts[client_id] = (window, count)
        return count <= limit, 60 - (now % 60)
