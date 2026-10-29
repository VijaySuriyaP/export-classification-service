"""Environment-only configuration; no provider secret or model identifier is embedded."""
from __future__ import annotations

import os


def env_int(name: str, default: int) -> int:
    """Read a positive integer from the environment, falling back safely."""
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def get_setting(name: str, default: str = "") -> str:
    """Return an environment setting without logging its value."""
    return os.getenv(name, default)


DATABASE_URL = get_setting("DATABASE_URL", "sqlite:///./exporter.db")
REDIS_URL = get_setting("REDIS_URL", "redis://localhost:6379/0")
VERIFIER_URL = get_setting("VERIFIER_URL", "")
PROMPT_VERSION = get_setting("PROMPT_VERSION", "v1")
MAX_STEPS = env_int("MAX_STEPS", 8)
MAX_TOOL_CALLS = env_int("MAX_TOOL_CALLS", 16)
MAX_WALL_CLOCK_S = env_int("MAX_WALL_CLOCK_S", 30)
RATE_LIMIT_PER_MIN = env_int("RATE_LIMIT_PER_MIN", 60)
