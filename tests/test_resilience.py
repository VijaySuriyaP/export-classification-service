"""Circuit-breaker and retry utility tests."""
import pytest
from src.common.resilience import CircuitBreaker, retry_call


def test_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreaker(threshold=1, reset_s=30)
    with pytest.raises(ValueError):
        breaker.call(lambda: (_ for _ in ()).throw(ValueError("expected test failure")))
    assert breaker.state == "open"
    with pytest.raises(RuntimeError, match="open"):
        breaker.call(lambda: 1)


def test_retry_returns_after_transient_failure() -> None:
    calls = {"count": 0}
    def sometimes() -> str:
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError("transient test failure")
        return "ok"
    assert retry_call(sometimes, attempts=2, base_delay_s=0) == "ok"
