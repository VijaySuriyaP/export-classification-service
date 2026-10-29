"""Test configuration uses an isolated local SQLite database and no Redis dependency."""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./tests/test_exporter.db")
os.environ.setdefault("REDIS_REQUIRED", "false")
os.environ["VERIFIER_URL"] = ""

import pytest  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from src.api.queue import reset_memory_queue  # noqa: E402
from src.common.db import SessionLocal, init_db  # noqa: E402
from src.common.db import CostLedger, EvalScore, FeedbackRecord, IndexFreshness, QuarantineRecord, RunRecord, RunStep  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    """Reset database rows and queue for repeatable test isolation."""
    init_db()
    with SessionLocal() as session:
        for table in (CostLedger, EvalScore, FeedbackRecord, RunStep, QuarantineRecord, RunRecord, IndexFreshness):
            session.execute(delete(table))
        session.commit()
    reset_memory_queue()
    yield
    reset_memory_queue()
