"""Ordered General Rules for Interpretation checklist helper."""
from __future__ import annotations

GRI_ORDER = ("GRI-1", "GRI-2", "GRI-3(a)", "GRI-3(b)", "GRI-3(c)", "GRI-4", "GRI-5", "GRI-6")


def rule_order(identifier: str) -> int | None:
    """Return the intended GRI order, or None for unknown identifiers."""
    normalized = identifier.strip().replace(" ", "")
    aliases = {"GRI-3a": "GRI-3(a)", "GRI-3b": "GRI-3(b)", "GRI-3c": "GRI-3(c)"}
    normalized = aliases.get(normalized, normalized)
    try:
        return GRI_ORDER.index(normalized)
    except ValueError:
        return None


def respects_gri_order(identifiers: list[str]) -> bool:
    """Return whether recognized GRI references are non-decreasing in order."""
    positions = [rule_order(item) for item in identifiers]
    positions = [item for item in positions if item is not None]
    return positions == sorted(positions)
