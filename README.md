# Export Classification Check Service

Docker Compose reference implementation for a review-first export classification workflow. It accepts a product description, validates the request, searches available official tariff passages, hands a typed result to an independent verifier, returns a route and citations, and **never files a declaration**. A licensed customs broker makes the final decision.

The project prioritizes a runnable offline walking skeleton. If current official tariff and export-policy documents have not been downloaded and inspected, it escalates without asserting an HS code or export policy. That is intentional, not a stub classification.

## Quick start

Prerequisite: Docker Engine with Docker Compose v2. Nothing else is required on the host for the service or smoke test.

```bash
cp .env.example .env
# Change POSTGRES_PASSWORD and keep DATABASE_URL in sync for any non-demo environment.
docker compose up --build -d
bash scripts/smoke.sh
```

The smoke script waits for API readiness, submits a valid request from inside the API container, polls the run to a terminal state, and prints the result. The default provider is offline/stub and costs nothing. It may still need Docker images to be pulled once.

Open the web client at http://localhost:8080 and FastAPI docs at http://localhost:8000/docs. API metrics are at http://localhost:8000/metrics. `docker compose ps` and `docker compose logs -f api agent-worker verifier` help inspect runtime status.

## Example API request

```bash
curl -sS http://localhost:8000/v1/classify \
  -H 'content-type: application/json' \
  -d '{"client_request_id":"11111111-1111-4111-8111-111111111111","product_description":"Stainless steel vacuum flask for carrying hot drinks","materials":["stainless_steel"],"intended_use":"Reusable drink container","destination_country":"US","client_id":"demo-client"}'
```

The endpoint returns HTTP `202` with a `run_id`. Poll `GET /v1/runs/{run_id}` until `completed` or `failed_escalated`. A result carries `route`, `basis`, `proposed_hs_code` (null while unsupported), `rule_applied`, `citations`, `export_policy`, `escalation_path`, `prompt_version`, `degraded`, trace data, and the mandatory broker-review disclaimer.

## Official corpus setup (required for actual tariff-grounded candidates)

No tariff text is bundled or invented. See [`corpus/SOURCES.md`](corpus/SOURCES.md) for the required current documents:

- Current CBIC Customs Tariff First Schedule, including General Rules for Interpretation (GRI), General Notes, Section Notes, and Chapters 73 and 96.
- Current notified DGFT ITC(HS) Schedule-II Export Policy and General Notes to Export Policy.

Download only from the current official CBIC/DGFT pages, record the notification/effective dates, and put the PDFs in `corpus/raw/`. Optionally set `CBIC_TARIFF_PDF_URL` and `DGFT_SCHEDULE_II_PDF_URL` to current official direct download URLs before running `bash scripts/download_corpus.sh`. Then run:

```bash
make index
docker compose exec -T agent-worker python scripts/inspect_corpus.py
```

The current indexing implementation is lexical JSONL with source/page/hash metadata. It does not yet run OCR automatically or embed into Chroma; these limits are documented. Manually verify extracted official passages before relying on them. The section 4.1 vacuum-flask case remains unconfirmed until the actual heading/GRI passages are checked.

## Commands

```bash
make test                 # pytest in a disposable Python 3.11 container
make index                # parse PDFs in corpus/raw and update lexical JSONL
make eval                 # live API evaluation; see status fields in eval/scenarios.jsonl
make load                 # concurrency sweep; SLO is declared in docs/SLO.md
make smoke                # compose startup + valid submit/poll test
make lint                 # Ruff inside the selected environment
python scripts/resume_check.py
```

Optional profiles:

```bash
docker compose --profile corpus up -d --build   # Chroma/indexer; Chroma integration remains partial
docker compose --profile observability up -d    # Prometheus, Grafana, Jaeger starter services
```

URLs in the observability profile: Prometheus http://localhost:9090, Grafana http://localhost:3000, Jaeger UI http://localhost:16686. Full OTEL propagation and production-grade dashboards are deferred.

## API surface

- `POST /v1/classify` — field-level validation; invalid input is written to `quarantine` and never queued.
- `GET /v1/runs/{run_id}` — status and terminal proposal/review route.
- `GET /v1/runs/{run_id}/trace` — persisted request, result and ordered steps.
- `POST /v1/runs/{run_id}/feedback` and `GET /v1/feedback/summary` — feedback capture.
- `/healthz`, `/readyz`, `/metrics` — probes and Prometheus metrics.

## Project map

`src/api` is the gateway; `src/worker` consumes Redis; `src/agent` contains evidence retrieval and GRI helpers; `src/verifier` checks the typed handoff; `src/llm` has the provider interface; `src/indexer` handles source PDFs; `src/guardrails` checks untrusted text and output; `src/eval` has metrics and runner; `contracts` has JSON schemas; `prompts` has versioned artifacts; `docs` contains decisions/runbook/submission status.

## Limitations and safe operating stance

This is a student-project reference implementation, not a legal service. Current source PDFs are not included; the full LangGraph model-selected loop, Chroma semantic search, live per-call cost/budget control, full circuit-breaker integration, OpenTelemetry, comprehensive Grafana panels, live-scored quality trends and actual load/evaluation results are incomplete. The `PROGRESS.md`, `STATE.md`, `docs/PRIORITIES.md`, and `SUBMISSION.md` state what is implemented versus deferred. Docker-dependent acceptance has not been verified in any environment without Docker.
