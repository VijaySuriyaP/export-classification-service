"""Evidence-first agent flow refuses to invent classifications without corpus."""
from uuid import uuid4
from src.agent.graph import classify_request


def test_empty_corpus_escalates_without_code(tmp_path, monkeypatch) -> None:
    from src.agent import tools
    monkeypatch.setattr(tools, "INDEX_PATH", tmp_path / "missing.jsonl")
    request = {"client_request_id": str(uuid4()), "product_description": "A stainless steel vacuum flask for hot drinks",
        "materials": ["stainless_steel"], "destination_country": "US", "client_id": "test"}
    result = classify_request("run-1", request)
    assert result.route.value == "specialist-classification-review"
    assert result.proposed_hs_code is None
    assert "not indexed" in result.basis
