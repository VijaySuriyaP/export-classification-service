"""Worker-to-result integration check in local SQLite/stub mode."""
from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from src.api.main import app
from src.common.db import RunRecord, SessionLocal
from src.worker.tasks import execute_run

client = TestClient(app)


def test_run_worker_escalates_without_official_corpus() -> None:
    payload = {"client_request_id": str(uuid4()), "product_description": "Stainless steel vacuum flask for carrying hot drinks",
        "materials": ["stainless_steel"], "destination_country": "US", "client_id": "worker-test"}
    submitted = client.post("/v1/classify", json=payload)
    assert submitted.status_code == 202
    run_id = submitted.json()["run_id"]
    result = execute_run(run_id)
    assert result is not None
    assert result["route"] == "specialist-classification-review"
    assert result["proposed_hs_code"] is None
    assert result["disclaimer"]
    with SessionLocal() as session:
        record = session.get(RunRecord, run_id)
        assert record is not None and record.status == "completed"
