"""Environment-priced token cost helper; returns zero when prices are unset."""
from __future__ import annotations

import os


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimate a call cost using environment price per thousand tokens."""
    in_price = float(os.getenv("LLM_PRICE_IN_PER_1K", "0") or 0)
    out_price = float(os.getenv("LLM_PRICE_OUT_PER_1K", "0") or 0)
    return max(0, input_tokens) * in_price / 1000 + max(0, output_tokens) * out_price / 1000
