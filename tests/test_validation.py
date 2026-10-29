"""Data-contract validation and quarantine tests."""
from __future__ import annotations

from uuid import uuid4

from src.api.validation import validate_request


def valid_request() -> dict:
    """Build a representative valid request."""
    return {"client_request_id": str(uuid4()), "product_description": "Stainless steel vacuum flask for carrying hot drinks",
        "materials": ["stainless_steel"], "destination_country": "US", "client_id": "test-client"}


def test_valid_request() -> None:
    model, errors = validate_request(valid_request())
    assert model is not None
    assert errors == []


def test_unit_value_requires_currency() -> None:
    raw = valid_request() | {"unit_value": 25.0}
    model, errors = validate_request(raw)
    assert model is None
    assert any("currency is required" in item["message"] for item in errors)


def test_hs_hint_chapter_is_checked() -> None:
    model, errors = validate_request(valid_request() | {"hs_hint": "x733"})
    assert model is None
    assert errors


def test_callback_must_be_allowlisted_https() -> None:
    model, errors = validate_request(valid_request() | {"callback_url": "http://example.com/hook"})
    assert model is None
    assert errors


def test_extra_fields_are_rejected() -> None:
    model, errors = validate_request(valid_request() | {"admin": True})
    assert model is None
    assert any(item["field"] == "admin" for item in errors)


def test_unknown_iso_country_code_is_rejected() -> None:
    model, errors = validate_request(valid_request() | {"destination_country": "ZZ"})
    assert model is None
    assert any(item["field"] == "destination_country" for item in errors)
