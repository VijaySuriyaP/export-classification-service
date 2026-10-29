"""Redis list consumer for queued classification requests."""
from __future__ import annotations

import logging
import os
import time

import redis

from src.api.queue import QUEUE_NAME
from src.common.db import init_db
from src.worker.tasks import execute_run

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def main() -> None:
    """Consume run identifiers until the container is stopped."""
    init_db()
    client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
    while True:
        try:
            entry = client.blpop(QUEUE_NAME, timeout=5)
            if entry:
                execute_run(entry[1])
        except Exception:
            logger.exception("worker loop failure; retrying after short delay")
            time.sleep(2)


if __name__ == "__main__":
    main()
