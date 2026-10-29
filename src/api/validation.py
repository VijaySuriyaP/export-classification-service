"""Request validation returning stable field-level errors for quarantine."""
from __future__ import annotations

from typing import Any
from pydantic import ValidationError

from src.common.models import ClassifyRequest


def validate_request(raw: Any) -> tuple[ClassifyRequest | None, list[dict[str, Any]]]:
    """Validate a raw request and normalize Pydantic errors to API contract."""
    try:
        return ClassifyRequest.model_validate(raw), []
    except ValidationError as exc:
        errors = []
        for error in exc.errors(include_url=False):
            errors.append({
                "field": ".".join(str(part) for part in error.get("loc", [])) or "$",
                "code": error.get("type", "validation_error"),
                "message": error.get("msg", "invalid value"),
            })
        return None, errors
