"""Test configuration uses an isolated local SQLite database and no Redis dependency."""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./tests/test_exporter.db")
os.environ.setdefault("REDIS_REQUIRED", "false")
os.environ["VERIFIER_URL"] = ""

import pytest
from sqlalchemy import delete

from src.api.queue import reset_memory_queue
from src.common.db import SessionLocal, init_db
from src.common.db import CostLedger, EvalScore, FeedbackRecord, IndexFreshness, QuarantineRecord, RunRecord, RunStep


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
