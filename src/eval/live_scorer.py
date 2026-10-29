"""Small helper to persist already-computed scores for quality trend reporting."""
from __future__ import annotations

from typing import Any
from src.common.db import EvalScore, SessionLocal


def save_score(run_id: str, metrics: dict[str, Any]) -> None:
    """Store a score payload associated with a run ID."""
    with SessionLocal() as session:
        session.add(EvalScore(run_id=run_id, metrics=metrics))
        session.commit()
