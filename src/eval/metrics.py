"""Deterministic, explainable evaluation metric helpers for stub/offline runs."""
from __future__ import annotations

from typing import Any


def groundedness(claims: list[str], passages: list[str]) -> float | None:
    """Fraction of non-empty claims sharing at least one token with evidence."""
    if not claims:
        return None
    evidence = set(" ".join(passages).lower().split())
    return sum(bool(set(claim.lower().split()) & evidence) for claim in claims) / len(claims)


def context_relevance(relevant_flags: list[bool]) -> float | None:
    """Fraction of retrieved passages manually/heuristically marked relevant."""
    return sum(relevant_flags) / len(relevant_flags) if relevant_flags else None


def faithfulness(citations_resolve: list[bool]) -> float | None:
    """Fraction of citations resolving to retrieved evidence."""
    return sum(citations_resolve) / len(citations_resolve) if citations_resolve else None


def hallucination_rate(run_has_unsupported_claim: list[bool]) -> float | None:
    """Fraction of runs containing at least one unsupported claim/citation."""
    return sum(run_has_unsupported_claim) / len(run_has_unsupported_claim) if run_has_unsupported_claim else None


def evaluation_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute route accuracy and stub-compatible evidence metrics over result rows."""
    scored = [row for row in rows if row.get("expected_route") and row.get("corpus_status") != "needs_corpus_confirmation"]
    route_accuracy = (sum(row.get("route") == row["expected_route"] for row in scored) / len(scored)) if scored else None
    return {"scenario_count": len(rows), "scored_scenario_count": len(scored), "route_accuracy": route_accuracy,
        "groundedness": groundedness([str(row.get("basis", "")) for row in rows], [str(row.get("evidence_text", "")) for row in rows]),
        "context_relevance": context_relevance([bool(row.get("evidence_text")) for row in rows]),
        "faithfulness": faithfulness([bool(row.get("citations_resolved")) for row in rows if row.get("citations")]),
        "hallucination_rate": hallucination_rate([bool(row.get("unsupported_claim")) for row in rows]),
        "note": "Deterministic lexical estimates, not an LLM judge; scenarios need corpus confirmation before gold-score interpretation."}
