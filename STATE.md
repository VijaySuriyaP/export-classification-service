# Current state — resumable checkpoint

- **Repository:** `export-classification-service`
- **Critical next step:** Step 12, the walking-skeleton acceptance gate. The code is drafted, but the gate must not be marked complete until a real Docker Compose smoke test passes.
- **Exact next command:** `cp .env.example .env && docker compose down -v --remove-orphans && bash scripts/smoke.sh`
- **Environment limitation:** Docker/Compose are not installed in the build workspace. The Compose YAML parses, but no container build/start/health/request test has been observed here.
- **Latest local test result:** `python -m compileall -q src tests scripts loadtest` passed; `pytest -q` returned **24 passed** in Python 3.13.5. Container images target Python 3.11.
- **Ruff:** unverified; installation failed due package-index DNS failure. See `docs/INCIDENT_LOG.md`.
- **Official corpus:** no PDFs are bundled and no tariff text is invented. Download the current official documents listed in `corpus/SOURCES.md` into `corpus/raw/`; then run `make index` and inspect the output against the original PDFs.

## Key decisions

- Python image target: 3.11.
- Default model provider: `stub`; external provider URL/key/model/prices are environment-only. The current classification graph does not need external LLM calls.
- `LLM_DRY_RUN=true` by default.
- Container ports: API 8000, web 8080, stub 8001, verifier 8002, Chroma optional profile 8004, Prometheus/Grafana/Jaeger optional profile 9090/3000/16686.
- Queue: Redis list `export:runs`; PostgreSQL database configured by `DATABASE_URL`.
- Durable tables: `runs`, `run_steps`, `quarantine`, `feedback`, `index_freshness`, `eval_scores`, `cost_ledger`.
- API: `POST /v1/classify` returns 202; polling `GET /v1/runs/{id}`; trace `GET /v1/runs/{id}/trace`; feedback `POST /v1/runs/{id}/feedback`; readiness `/readyz`; metrics `/metrics`.
- Prompt versions: `v1`, `v2`, selected by `PROMPT_VERSION` environment setting.
- SLO: 60-second end-to-end p95 target, declared before any load measurements in `docs/SLO.md`; actual load results do not exist.
- Retrieval: lexical `corpus/processed/chunks.jsonl`; semantic embeddings and Chroma upsert remain deferred.

## Known limitations / outstanding work

- Step 12 Compose smoke gate remains the first unchecked critical step.
- Current CBIC tariff/GRI/Chapters 73 and 96 and DGFT Schedule-II PDFs are not bundled/indexed; a safe review route is the expected output while sources are missing.
- Full LangGraph model-selected loop, complete note/policy extraction, OCR execution, semantic embeddings, provider breaker integration, reliable queue redelivery, OTEL, complete metrics/Grafana, cost/budget enforcement and integrated cache are incomplete.
- Scenario set is a coverage scaffold; every row says `needs_corpus_confirmation` until actual official source text and gold labels are reviewed.
- No prompt comparison, deliberate-change values, performance values, scaling results or cost benchmarks have been fabricated.

## Resume procedure

1. Read `PROGRESS.md` and this file.
2. Run `python scripts/resume_check.py` (with Python available) or use the first unchecked step listed in `PROGRESS.md`.
3. Finish Step 12 first on a Docker host. Only mark it passed after `bash scripts/smoke.sh` submits a request and sees a terminal result.
4. Continue only after the skeleton gate succeeds. Add official corpus PDFs, verify passages, then run tests/evaluation/load experiments and retain actual results.
