# Fallback path

1. The default provider is `stub`, and the production classification graph is evidence-first; it is safe to run offline.
2. The optional OpenAI-compatible adapter requires `LLM_BASE_URL`, `LLM_MODEL_PRIMARY`, and optionally `LLM_API_KEY`, all from environment variables. Prices are also environment-only.
3. `CHAOS_PROVIDER_DOWN=true` intentionally fails the optional provider adapter for a demo. `CircuitBreaker` and `retry_call` are standalone utilities; their full integration into the agent request path remains deferred.
4. If the verifier service is unreachable, the worker produces `specialist-classification-review`, sets `degraded=true`, and asserts no HS code. If a worker processing path fails, the run is recorded as `failed_escalated` with no HS code.
5. Empty/stale index: run `make index`, inspect `corpus/processed/index_status.json`, then use `scripts/inspect_corpus.py`. Do not substitute unofficial fixture text.
