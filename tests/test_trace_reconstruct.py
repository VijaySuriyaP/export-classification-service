"""Run trace API responds consistently for unknown IDs."""
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_missing_trace_returns_404() -> None:
    response = client.get("/v1/runs/not-a-real-run/trace")
    assert response.status_code == 404
