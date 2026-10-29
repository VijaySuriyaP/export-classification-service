"""Dependency-free conservative toxicity screen for demo inputs."""
from __future__ import annotations

import re

_TERMS = {"kill yourself", "racial slur", "threaten to harm", "dox this person"}


def is_toxic(value: str) -> bool:
    """Return True for a small explicit set of high-risk abusive phrases."""
    normalized = re.sub(r"\s+", " ", value.lower())
    return any(term in normalized for term in _TERMS)
