"""Small Redis cache helper; safe no-cache fallback when Redis is unavailable."""
from __future__ import annotations

import hashlib
import json
import os


def cache_key(description: str, materials: list[str], prompt_version: str, index_version: str) -> str:
    """Build a deterministic cache key over normalized request content and versions."""
    payload = json.dumps([" ".join(description.lower().split()), sorted(materials), prompt_version, index_version])
    return "export:cache:" + hashlib.sha256(payload.encode()).hexdigest()


def get_redis_client():
    """Return Redis client if the optional package and connection are available."""
    try:
        import redis

        client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None
