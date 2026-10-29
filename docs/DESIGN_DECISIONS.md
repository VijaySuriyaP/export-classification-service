# Design decisions

## Implemented

1. **Asynchronous API:** `POST /v1/classify` returns `202` with `run_id`; clients poll `GET /v1/runs/{run_id}`. Classification may involve slow retrieval, policy checks, and a separate verifier; synchronous requests risk client/proxy timeouts and make workers hard to scale.
2. **Redis queue + PostgreSQL state:** Redis is suitable for lightweight queue hand-off; PostgreSQL remains the durable source of truth for runs, quarantine, feedback and trace steps.
3. **Offline stub default:** no external provider is needed to start the demo and no cost/credential is incurred. An OpenAI-compatible provider adapter reads base URL, model name, API key and token prices only from environment variables.
4. **Evidence-first escalation:** absence of verified source PDFs must not be replaced with memorized or fabricated tariff text. The system routes to specialist review and emits no HS code when evidence is missing.
5. **Independent verifier:** citation IDs/identifiers are validated against the hand-off passage set in a separate service. Verifier outage suppresses confidence and sets `degraded=true`.
6. **Lexical JSONL index first:** this creates a lightweight and inspectable walking skeleton. Embedding vectors, semantic retrieval and Chroma upserts remain deferred; the optional Chroma service is not silently claimed to be wired in.
7. **Fixed-window rate limit first:** simple, transparent Redis per-client request limiting was chosen over a distributed token bucket for the initial working skeleton.

## Rejected / deferred alternatives

- **Synchronous classification:** rejected because work duration and retries make request timeouts likely.
- **LLM-only HS answers:** rejected because plausible but uncited tariff text can create compliance risk.
- **Bundled example tariff snippets:** rejected because examples may be mistaken for official or current law.
- **Immediate LangGraph agentic tool loop:** deferred until corpus retrieval and a stable walking skeleton are verified. Current graph is bounded and deterministic; it does not claim dynamic model-selected tools.
- **Mandatory semantic vector index in the default `up`:** deferred to avoid making the critical skeleton depend on a separate heavy service before there is a corpus to index.
