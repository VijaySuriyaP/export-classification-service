# Priorities: built, partial, deferred

## P0 — protect the demo from failing silently
- Implemented: Compose walking-skeleton topology for API, worker, Redis, PostgreSQL, verifier, static web and stub service; 202 submit/poll contract; health/readiness; validation/quarantine; default offline processing.
- **Not verified here:** Docker Compose parsing, clean `docker compose up`, cross-container smoke test and scaling. Docker is absent in the current environment; Step 12 remains unchecked.

## P1 — avoid invented classifications
- Implemented: official-only input corpus location, PDF text extraction, lexical heading search, source metadata, conservative verifier, safe escalation with null code if evidence is absent.
- Deferred: confirmed current official PDFs, robust OCR, full note extraction, complete chapter policy rows, vector embeddings/Chroma indexing, human-confirmed vacuum-flask evidence.

## P2 — independent agent and resilience features
- Implemented: separate verifier service, typed `HandoffPayload`, trace records, injection/output filter helpers, timeout-bounded verifier HTTP, standalone retry and circuit-breaker utilities.
- Partial/deferred: model-selected LangGraph loop, provider breaker in live path, end-to-end agent retries, complete worker redelivery semantics, OpenTelemetry, all-service metrics, cost budget enforcement.

## P3 — evaluation and operations
- Implemented: scenario coverage scaffold, deterministic metric functions, live eval CLI, runbook, demo scripts, report and requirement mapping.
- Deferred until runtime/source setup: gold-label confirmation, prompt comparison output, deliberate-change experiment, SLO load measurement, worker-scale comparison, cost/latency results and full Grafana panels.

See `PROGRESS.md` and `SUBMISSION.md` for step-level status and mappings.
