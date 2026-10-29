"""Deterministic evaluation metrics tests."""
from src.eval.metrics import context_relevance, faithfulness, groundedness, hallucination_rate


def test_metrics_compute_expected_small_fractions() -> None:
    assert groundedness(["steel flask"], ["steel flask heading"]) == 1.0
    assert context_relevance([True, False]) == 0.5
    assert faithfulness([True, False]) == 0.5
    assert hallucination_rate([False, True]) == 0.5
