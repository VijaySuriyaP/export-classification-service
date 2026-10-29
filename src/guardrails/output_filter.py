"""Enforce proposal-only wording and remove risky markup from outputs."""
from __future__ import annotations

import re
from typing import Any

from src.common.models import Route

DISCLAIMER = (
    "This is a proposed classification check, not a legal determination. "
    "A licensed customs broker must decide before any filing."
)
_BLOCKED = re.compile(r"\b(approved|licence granted|license granted|final classification|declaration filed)\b", re.I)


def filter_result(value: dict[str, Any]) -> dict[str, Any]:
    """Normalize the public response, enforce safe defaults and disclaimer."""
    result = dict(value)
    for key in ("basis", "rule_applied"):
        if isinstance(result.get(key), str):
            text = _BLOCKED.sub("review required", result[key])
            text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
            result[key] = re.sub(r"https?://\S+", "[link removed]", text)
    try:
        route = Route(result.get("route"))
    except ValueError:
        route = Route.SPECIALIST_CLASSIFICATION_REVIEW
    if route != Route.CLEAR_FOR_FILING:
        result["proposed_hs_code"] = None
        result["rule_applied"] = None
        result["export_policy"] = None
    result["route"] = route.value
    result["disclaimer"] = DISCLAIMER
    result.setdefault("citations", [])
    result.setdefault("escalation_path", [])
    result.setdefault("degraded", False)
    result.setdefault("prompt_version", "v1")
    return result
