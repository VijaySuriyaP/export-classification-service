"""Verifier citation resolution and conservative escalation checks."""
from fastapi.testclient import TestClient
from src.verifier.app import app

client = TestClient(app)


def test_review_without_claim_is_verified_as_safe_escalation() -> None:
    payload = {"run_id": "r1", "request": {}, "route": "specialist-classification-review", "basis": "no source", "passages": [], "citations": []}
    response = client.post("/verify", json=payload)
    assert response.status_code == 200
    assert response.json()["verified"] is True


def test_unresolved_citation_fails() -> None:
    payload = {"run_id": "r1", "request": {}, "route": "specialist-classification-review", "basis": "review",
        "passages": [], "citations": [{"chunk_id": "missing", "identifier": "GRI-1", "doc": "source.pdf", "excerpt": "rule text"}]}
    response = client.post("/verify", json=payload)
    assert response.status_code == 200
    assert response.json()["verified"] is False
