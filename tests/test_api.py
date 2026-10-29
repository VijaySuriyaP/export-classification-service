"""Async API and quarantine behavior checks."""
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from src.api.main import app
from src.api.queue import queue_length
from src.common.db import QuarantineRecord, SessionLocal

client = TestClient(app)


def payload() -> dict:
    """Return an API-valid request body."""
    return {"client_request_id": str(uuid4()), "product_description": "Stainless steel vacuum flask for carrying hot drinks",
        "materials": ["stainless_steel"], "destination_country": "US", "client_id": "api-test"}


def test_submit_returns_202_and_run_id() -> None:
    response = client.post("/v1/classify", json=payload())
    assert response.status_code == 202
    assert response.json()["run_id"]
    assert response.json()["status"] == "queued"
    assert queue_length() == 1


def test_invalid_request_is_quarantined_without_enqueue() -> None:
    before = queue_length()
    response = client.post("/v1/classify", json={"product_description": "x"})
    assert response.status_code == 422
    assert response.json()["quarantined"] is True
    assert queue_length() == before
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(QuarantineRecord)) == 1


def test_health_and_ready() -> None:
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 200
