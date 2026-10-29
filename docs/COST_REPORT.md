# Cost report

**Status: NOT MEASURED.** Default runs use the deterministic evidence-first path and make no LLM completion calls. Provider-price inputs are read from `LLM_PRICE_IN_PER_1K` and `LLM_PRICE_OUT_PER_1K`, but a production-quality live per-call ledger/budget refusal is not integrated. Do not report estimated provider cost as an actual measured cost.

For a configured compatible provider, capture provider usage at call time, set prices from the provider's current pricing page, and report measured tokens and cost per run and per 100 runs. Never commit credentials or provider-specific secrets.
