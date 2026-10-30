# Project progress checklist

`[x]` means the implementation/source exists; it does not mean every runtime or corpus acceptance gate passed. `[ ]` means the requirement remains incomplete or the required evidence has not been produced.

## Phase 0 — scaffolding
- [x] Step 1: `README.md`, `.gitignore`, `.env.example`, `Makefile`. Produced environment-only configuration and common commands; verify with `cat .env.example` and Compose configuration.
- [x] Step 2: `PROGRESS.md`, `STATE.md`, `docs/PRIORITIES.md`, `scripts/resume_check.py`. Verify with `python scripts/resume_check.py`.
- [x] Step 3: `docs/ARCHITECTURE.md`, `docs/DESIGN_DECISIONS.md`. Contains deployment boundaries, rationale and deferred choices.

## Phase 1 — walking skeleton (critical)
- [x] Step 4: request/response JSON contracts, `src/common/models.py`, `docs/DATA_CONTRACT.md`; verify `pytest -q tests/test_validation.py`.
- [x] Step 5: `src/common/config.py`, structured logging and SQLAlchemy tables in `src/common/db.py`; verify API readiness/table initialization.
- [x] Step 6: `src/api/validation.py`, `tests/test_validation.py`; actual local result: validation tests pass.
- [x] Step 7: `src/api/main.py`, `src/api/queue.py`, `src/api/ratelimit.py`; actual local API/quarantine tests pass.
- [x] Step 8: `src/llm/provider.py`, `src/llm_stub/app.py`; provider is env-configured, stub is offline.
- [x] Step 9: `src/worker/tasks.py`, `src/worker/main.py`, `docker/Dockerfile.api`, `docker/Dockerfile.worker`; local worker integration test passes.
- [x] Step 10: `docker-compose.yml`, service Dockerfiles, `scripts/smoke.sh`; Compose configuration and runtime service startup were verified.
- [x] Step 11: `web/index.html`, `web/app.js`, nginx config; browser verification remains pending.
- [x] Step 12: clean Compose walking-skeleton gate and `skeleton-ok` tag. Verified with clean Compose smoke runs, web health, and three healthy workers; see `verification/logs/B_smoke_final.txt`, `verification/logs/B_final_ps.txt`, and `verification/logs/B_final_scale3.txt`. The web healthcheck was corrected to probe IPv4 loopback because Alpine resolved `localhost` to IPv6.

## Phase 2 — official corpus and indexing
- [x] Step 13: `corpus/SOURCES.md`, `scripts/download_corpus.sh`; official source starting points and version/effective-date instructions are present. PDFs are not bundled.
- [x] Step 14: `src/indexer/parse.py`; PDF page extraction and OCR-needed marker exist; actual current PDFs/OCR flow not verified.
- [x] Step 15: `src/indexer/chunk.py`, `docs/CHUNKING_EMBEDDING.md`; structural chunking and metadata are unit-tested with clearly labelled non-official test text.
- [ ] Step 16: semantic embeddings, Chroma upsert and selective re-embedding. Current implementation is lexical JSONL only; vector integration deferred.
- [x] Step 17: `tests/test_chunk.py`, `tests/test_indexer_idempotent.py`, `scripts/inspect_corpus.py`; unit tests pass. Vacuum-flask passages still require official corpus confirmation.

## Phase 3 — agents
- [x] Step 18: six retrieval/request/policy tools in `src/agent/tools.py`; corpus-dependent relevance not evaluated without official PDFs.
- [x] Step 19: `prompts/v1/`, `prompts/v2/`, `src/agent/prompt_store.py`; prompt version is included in run results/step traces.
- [ ] Step 20: full LangGraph/model-selected tool loop. Current bounded deterministic graph is in `src/agent/graph.py`; LangGraph integration and genuinely dynamic tool selection deferred.
- [x] Step 21: `src/agent/gri.py`, `src/agent/entities.py`; rule-order helper and structured entity extraction exist.
- [x] Step 22: separate `src/verifier/app.py`, `docker/Dockerfile.verifier`; exact handoff citation resolution unit-tested. Semantic entailment verification remains basic.
- [x] Step 23: worker-to-verifier typed handoff and degraded route in `src/worker/tasks.py`; Docker/network integration not run.
- [ ] Step 24: corpus-backed tie, unsupported-answer and section 4.1 vacuum-flask evaluation; deferred until current official text is indexed and human-confirmed.

## Phase 4 — guardrails and reliability
- [x] Step 25: input normalization/injection screen in `src/guardrails/injection.py`; unit tests pass.
- [x] Step 26: proposal-only output filter and toxicity fallback in `src/guardrails/output_filter.py`, `src/guardrails/toxicity.py`; heuristic only, not a security guarantee.
- [ ] Step 27: full provider retry/breaker/fallback/chaos integration. Helpers and provider adapter exist; live classification path does not currently invoke the provider.

## Phase 5 — observability and trace reconstruction
- [ ] Step 28: OpenTelemetry spans/propagation. Jaeger profile exists but trace wiring is deferred.
- [ ] Step 29: complete metrics in every service. API request/latency metrics and Prometheus starter exist; agent/queue/resource metrics remain partial.
- [ ] Step 30: token cost capture, cost-ledger attribution and budget rejection. Cost helper/table exist; end-to-end integration deferred.
- [x] Step 31: `GET /v1/runs/{run_id}/trace` and trace records in `src/common/db.py`; endpoint test passes for missing IDs, worker stores step details.
- [ ] Step 32: complete Grafana dashboards; two starter API panels only, full per-agent/quality panels deferred.

## Phase 6 — cache, rate limit, feedback
- [ ] Step 33: integrated Redis embedding/retrieval/run cache; key helper exists, cache is not integrated into request flow.
- [x] Step 34: per-client Redis fixed-window limiter in `src/api/ratelimit.py`; fallback behavior supports offline tests.
- [x] Step 35: feedback endpoints/tables implemented; automated live sampling and scoring are not wired into the request lifecycle.

## Phase 7 — evaluation and LLMOps
- [x] Step 36: 22 cases in `eval/scenarios.jsonl`, covering required categories; each has `status: needs_corpus_confirmation` and no invented gold tariff code.
- [x] Step 37: four deterministic metric helpers in `src/eval/metrics.py` and explanation in `docs/EVAL_METRICS.md`.
- [x] Step 38: live service evaluator in `src/eval/run_eval.py`; requires a running service and reviewed gold scenarios.
- [ ] Step 39: prompt comparison output and one deliberate-change before/after report. Utilities exist, but no fabricated result files; experiment not run.

## Phase 8 — SLO, load and scaling
- [x] Step 40: `docs/SLO.md` declares the end-to-end p95 target before any load measurement; file is kept as a separate SLO commit in repository history.
- [x] Step 41: end-to-end Locust polling scenario and concurrency sweep script; not run in this environment.
- [ ] Step 42: one-versus-three-worker measurements, failing concurrency, bottleneck analysis, caching and cost comparison. No measurements claimed.

## Phase 9 — docs, runbook and final QA
- [x] Step 43: `docs/RUNBOOK.md`, `docs/INCIDENT_LOG.md`; incident log contains the real Ruff-install and Docker-engine failures.
- [x] Step 44: ten demo scripts and `docs/DEMO_CHECKLIST.md`; some commands explicitly depend on Compose/corpus.
- [x] Step 45: final README, `docs/REPORT.md`, `SUBMISSION.md` requirement mapping.
- [ ] Step 46: clean-clone Compose smoke, secrets/provider grep and final QA remain. Container pytest and scale=3 verification passed; a clean-clone run and secrets audit are still outstanding.

## Verification performed in this workspace
- `python -m compileall -q src tests scripts loadtest` — pass.
- `pytest -q` — 24 passed.
- `docker compose config -q` — pass.
- Containerized Python 3.11 pytest — 24 passed; containerized Ruff — all checks passed.
- `docker compose up`, `scripts/smoke.sh`, and scale=3 verification — passed after starting Docker Desktop; real corpus indexing and load testing remain unrun because official PDFs are not present.
