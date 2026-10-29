# Submission evidence map

Status words: **implemented** means source exists; **partial** means only a minimal helper/startup scaffold exists; **deferred** means acceptance evidence is missing. File presence does not mean a Docker runtime gate or real-corpus evaluation passed.

| Requirement group | Evidence | Status / limitation |
|---|---|---|
| F1 — validated request contract | `contracts/classify_request.schema.json`, `src/common/models.py`, `src/api/validation.py` | Implemented; ISO codes checked against bundled static set, production maintenance still needed. |
| F2 — quarantine/no enqueue | `src/api/main.py`, `tests/test_api.py` | Implemented and unit-tested. |
| F3 — source-grounded classification | `src/agent/tools.py`, `src/agent/graph.py`, `corpus/SOURCES.md` | Partial; no current PDFs bundled, no asserted code when evidence is absent. |
| F4 — export policy | `policy_lookup` in `src/agent/tools.py` | Partial; exact current DGFT row is required and corpus is absent. |
| F5 — verifiable citations | `src/verifier/app.py`, `tests/test_verifier.py` | Implemented as reference resolution; semantic entailment checking remains basic. |
| F6 — route outcomes | `src/common/models.py`, `src/agent/graph.py` | Implemented conservative routes. |
| F7 — ambiguous/tie/out-of-scope escalation | `src/agent/graph.py`, `eval/scenarios.jsonl` | Conservative partial; corpus-confirmed tie behavior needs evaluation. |
| F8 — API/web demo | `src/api/main.py`, `web/` | Implemented; Compose smoke gate not run here. |
| A1 — six tools | `src/agent/tools.py` | Implemented lexical versions; retrieval quality depends on real indexed corpus. |
| A2 — typed agent handoff | `src/common/models.py`, `src/worker/tasks.py` | Implemented. |
| A3 — independent verifier | `src/verifier/app.py`, Compose service | Implemented reference resolver; no separate LLM semantic judge. |
| A4 — async run model | `src/api/main.py`, `src/api/queue.py`, `src/worker/main.py` | Implemented; requires live Compose test. |
| A5 — prompt-injection and output guardrails | `src/guardrails/` | Partial heuristic screens; not a security guarantee. |
| A6 — reconstructable trace | `/v1/runs/{id}/trace`, `src/common/db.py` | Partial; current trace omits future raw model/tool internals. |
| A7 — scale/retry behavior | `src/common/resilience.py`, loadtest files | Partial; not measured; worker crash redelivery policy not fully implemented. |
| A8 — environment-only provider config | `src/llm/provider.py`, `.env.example` | Implemented adapter; external provider path is optional and not part of default graph. |
| L1 — corpus ingestion | `src/indexer/parse.py`, `src/indexer/chunk.py`, `src/indexer/cli.py` | Partial lexical index; OCR run and Chroma/vector embeddings deferred. |
| L2 — prompt comparison | `src/eval/compare.py`, `prompts/v1`, `prompts/v2` | Code exists; no comparison result until actual eval runs. |
| L3 — deliberate-change experiment | `docs/EVAL_METRICS.md`, `src/eval/` | Deferred; no before/after numbers fabricated. |
| L4 — injection/unsafe input defenses | `src/guardrails/`, tests | Partial heuristics; not a complete classifier or toxicity model. |
| L5 — cost attribution | `src/common/cost.py`, `cost_ledger` table | Partial; per-call capture and daily budget refusal deferred. |
| L6 — live quality feedback | feedback endpoints, `src/eval/live_scorer.py` | Feedback storage implemented; automatic sampling/scoring not wired. |
| D1 — data contract | schemas and `docs/DATA_CONTRACT.md` | Implemented as documented. |
| D2 — corpus provenance | `corpus/SOURCES.md`, chunk metadata | Partial; current PDFs/source versions not supplied. |
| D3 — container reproducibility | `docker-compose.yml`, `docker/` | Built as code; clean startup not verified due Docker unavailable. |
| D4 — secret/provider config hygiene | `.env.example`, `.gitignore`, `src/llm/provider.py` | No real keys included; run grep/QA before publication. |
| D5 — observability | API `/metrics`, `observability/` | Partial starter; OTEL and complete dashboards deferred. |
| D6 — load test | `loadtest/locustfile.py`, `scripts/run_load.sh` | Defined but not run; `docs/LOAD_RESULTS.md` says not measured. |
| D7 — caching/rate limit/feedback | `src/api/ratelimit.py`, `src/common/cache.py`, feedback endpoint | Partial; cache integration deferred. |
| D8 — documentation/runbook/demo | `README.md`, `docs/`, `scripts/demo/` | Implemented; runtime acceptance still needs evidence. |

## Critical acceptance gates still outstanding

1. Run `cp .env.example .env`, set a private local DB password and match the URL, then `docker compose up --build -d` and `bash scripts/smoke.sh` on a Docker host.
2. Run `make test` in a clean container and `ruff check src tests scripts`.
3. Download current official CBIC and DGFT documents and human-verify extracted GRI, chapter-note, heading and policy passages before indexing.
4. Run corpus-backed scenario evaluation, prompt comparison, deliberate-change experiment and the one-vs-three-worker load test. Save result files and only then update measured-result sections.
