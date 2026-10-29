# MASTER PROMPT: Mini Project 07, Export Classification Check Service (UE24AM342AA5)

Paste everything between START and END into your coding agent (Claude Code, Cursor, Copilot Agent, etc.) inside an empty Git repo.
If you run out of tokens, paste the RESUME PROMPT at the bottom into a fresh session and it continues from where it stopped.

======================== START OF PROMPT ========================

## ROLE

You are a senior ML-platform / AgentOps engineer. Build a complete, production-style, Docker-Compose-deployed **multi-agent export classification check service** in a GitHub repo called `export-classification-service`.

**Domain:** Logistics and trade compliance. A product description comes in; the system validates it, proposes a Harmonized System (HS) tariff classification **with the rule applied and citations**, states the **export policy** for that classification, and **routes** the result. It never files a declaration; a licensed customs broker decides.

**Corpus (public, text-layer PDFs preferred, OCR otherwise):**
- Customs Tariff General Rules for Interpretation (GRI)
- Customs Tariff Chapters **73** and **96** with section and chapter notes
- DGFT export policy schedule (ITC-HS) for those chapters

**Out of scope:** model training, cloud deployment, duty calculation, shipping documentation.

---

## THE ONE THING THAT DECIDES THE GRADE

> If the system does not start with a single `docker compose up` and serve a valid request at the demo, the project gets **ZERO**, regardless of anything else.

Therefore: build a **walking skeleton first** (Phase 1: containers up, request in, stub result out, async polling works), then add depth in strict priority order. Completing all 22 requirements is NOT expected; sound prioritisation is assessed. Keep `docs/PRIORITIES.md` recording what was built, what was deferred, and why.

---

## CRITICAL WORKING RULES (NON-NEGOTIABLE)

You may run out of token budget at any moment. The user must be able to stop after ANY file and resume later.

1. **Small numbered steps.** Each step creates or edits **at most 1 to 3 files**. Keep every source file under ~250 lines; split modules if bigger.
2. **Every file complete and runnable the moment it is written.** No `TODO` stubs, no `...` placeholders. If something is deferred, write a minimal working version now and add an upgrade task to `PROGRESS.md`.
3. **`PROGRESS.md`** at repo root: checklist of ALL steps below (`[ ]`/`[x]`). After each step: tick it, add one line "produced + how to verify", then `git add -A && git commit -m "step N: <title>"`.
4. **`STATE.md`**: current step, key decisions (library versions, ports, env var names, table names, endpoint paths, SLO value once set), known issues, exact next command. Update after every step so a fresh session needs zero memory of this chat.
5. **At session start ALWAYS read `PROGRESS.md` and `STATE.md` first**, continue from the first unchecked step, never redo finished steps, never rewrite existing files unless a step says so or a test fails.
6. **After each code step run its smoke test** (`pytest -q tests/<module>`, or `docker compose config`, `curl`, etc.) and fix before moving on. Record the result in `PROGRESS.md`.
7. **Token economy.** Don't paste whole files into chat; don't re-explain. After each step print only: `Step N done: <files> | test: pass/fail | next: step N+1`.
8. **No secrets, endpoints or model identifiers in the repo (D4).** All provider URL, API key, model names, price-per-token values come from environment variables only; commit `.env.example` with blank/placeholder values; `.env` is gitignored. Grep for violations in the final QA step.
9. **Everything runs in containers.** Nothing required on the host except Docker.
10. **LLM behind an interface you control** (`LLMProvider` abstract class; backends: `openai_compatible` (works with Groq/Gemini-OpenAI-compat/OpenRouter/Ollama via base URL), `stub`). Switching provider = env change only. Default dev mode = `stub` so the system always runs offline and free.
11. **Honesty rules:** never invent tariff text. Real corpus passages must come from the downloaded official documents. For unit tests, a tiny clearly-labelled **`tests/fixtures/NOT_OFFICIAL_*.txt`** may be used; never index it into the real index. `docs/INCIDENT_LOG.md` must contain only **real** failures that actually occurred while building; log each genuine failure when it happens (symptom, cause, fix, time). Never fabricate incidents or measurements. Every number in the report comes from a results file.
12. Python 3.11, type hints, docstrings on public functions, `ruff`-clean, `pytest`.
13. Set `LLM_DRY_RUN`/stub whenever you test so you don't burn free-tier quota.

---

## ARCHITECTURE (implement this; record deviations in STATE.md)

**Containers (Docker Compose, each with healthcheck + `depends_on: condition: service_healthy`):**

| Service | Role | Why a separate boundary |
|---|---|---|
| `api` | FastAPI gateway: validation (data contract), quarantine, rate limit, submit, status, feedback, metrics | Independent release; cheap resource profile; protects workers from malformed input |
| `agent-worker` | Task runner consuming the queue; runs **Agent 1 (Researcher/Classifier)** LangGraph | CPU/LLM-bound, **scaled with `--scale agent-worker=3`** |
| `verifier` | **Agent 2 (Verifier/Router)** as its own HTTP service with its own tools, prompt and model config | Real second agent: failure isolation, separate scaling and prompt releases |
| `redis` | Queue broker (Celery or RQ), cache (embeddings/retrieval/run), rate-limit counters | Stateful dependency |
| `postgres` | Runs, steps trace, quarantine, feedback, index freshness, eval scores | Durable state |
| `chroma` | Vector store service | Independent scaling and re-embedding |
| `indexer` | One-shot idempotent ingestion job (read, parse, OCR-if-needed, chunk, embed, upsert) | Resource profile (embedding) separate from serving |
| `llm-stub` | Fixed responses after a configurable realistic delay; also usable as fake provider | Needed for load tests (D6) |
| `web` | Static web client (nginx) | Simple, no marks for appearance |
| `prometheus`, `grafana`, `jaeger`, (optional `otel-collector`) | Observability | Standard |

That is well over the required four services.

**Topology & hand-off (A2):**
`api` → queue → `agent-worker` (Agent 1: extract entities, plan, tool loop, GRI application, candidate ranking) → HTTP hand-off with a typed `HandoffPayload` (candidates, rules applied, retrieved passages with ids, trace) → `verifier` (Agent 2: independent check that every citation resolves to retrieved text and that claims are supported; decides route). If `verifier` is down/timeouts: bounded retry, then **escalate to specialist-classification-review with `degraded=true`**, never a confident answer. If `agent-worker` dies mid-run: task visibility timeout + max redelivery, run marked `FAILED_ESCALATED`, never returned as confident.

**Agent 1 tools (A1, >= 3, chosen by the agent, not a fixed stage):**
1. `corpus_search(query, filters)`: semantic search (chapter/kind filters) over the Chroma index.
2. `find_headings_naming_article(term)`: lexical/semantic search restricted to **heading titles across all indexed chapters** (this is what finds "Vacuum flasks" when the description only says "stainless steel flask").
3. `get_clause(identifier)`: exact lookup, e.g. `GRI-1`, `GRI-3(a)`, `Ch73/Note-1`, `Ch96/Heading-9617`.
4. `list_notes_for(heading_or_chapter)`: all section/chapter notes that modify/exclude.
5. `get_request_field(name)`: read the validated request's own fields.
6. `policy_lookup(hs_code)`: DGFT export-policy row (free/restricted/prohibited, conditions) with citation.

**Agent 1 loop (bounded by `MAX_STEPS`, `MAX_TOOL_CALLS`, `MAX_WALL_CLOCK_S` from env):**
extract article + materials → retrieve provision that appears to apply → determine whether any other provision modifies/excludes it and search for it (notes, exclusions) → **derive a new query from what was read** and search again (including heading-name search) → apply **GRI strictly in order (1, 2, 3(a), 3(b), 3(c), 4, 5, 6)** citing the rule used → propose candidate(s) + policy → hand off. If retrieval support is weak: retry with a different strategy (different filters/query rewrite) up to a limit, else escalate.

**Routing outcomes (F6):** `clear-for-filing` | `seek-product-clarification` | `specialist-classification-review`, each with a stated `basis`.
**Escalation (F7):** two headings equally supported after GRI 3, or product outside chapters 73/96 → `specialist-classification-review`, no classification asserted.

**Async model (A4):** `POST /v1/classify` returns `202 {run_id}` immediately; `GET /v1/runs/{run_id}` polling (plus optional `callback_url`). Justify in `docs/DESIGN_DECISIONS.md`: runs take tens of seconds, HTTP timeouts and worker scaling make sync a poor fit.

**Data contract (D1/F2):** `contracts/classify_request.schema.json` + Pydantic model. Fields (adjust and document): `client_request_id` (uuid), `product_description` (string 10 to 2000 chars), `materials` (array of enum), `intended_use` (optional string), `weight_grams` (number >0, <= bound), `unit_value` + `currency` (enum INR/USD/EUR; **cross-field: unit_value requires currency**), `destination_country` (ISO-3166 alpha-2 enum), `hs_hint` (optional, regex digits; **cross-field: if present chapter must be a valid chapter number**), `callback_url` (optional, https only, allowlist), `client_id`. Schema, type, range, categorical and cross-field validation before any agent starts. Rejects are written to the `quarantine` table with field-level errors and **never enqueue a run** (prove with a test that queue length is unchanged).

---

## STEP LIST (strict order; one step = 1 to 3 files; commit after each)

### PHASE 0: Scaffolding (priority: critical)
- **Step 1:** Repo skeleton: `README.md` (skeleton), `.gitignore`, `.env.example` (all env vars: `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL_PRIMARY`, `LLM_MODEL_FALLBACK`, `LLM_PRICE_IN_PER_1K`, `LLM_PRICE_OUT_PER_1K`, `EMBED_MODEL`, `EMBED_MODEL_VERSION`, `MAX_STEPS`, `MAX_TOOL_CALLS`, `MAX_WALL_CLOCK_S`, `LLM_TIMEOUT_S`, `TOOL_TIMEOUT_S`, `RETRY_MAX`, `BREAKER_FAIL_THRESHOLD`, `BREAKER_RESET_S`, `RATE_LIMIT_PER_MIN`, `DAILY_BUDGET_USD`, DB/Redis URLs, `OTEL_EXPORTER_OTLP_ENDPOINT`, `PROMPT_VERSION`; placeholders only), `Makefile` (`up`, `down`, `test`, `index`, `eval`, `load`, `demo`).
- **Step 2:** `PROGRESS.md` (full checklist), `STATE.md`, `docs/PRIORITIES.md`, `scripts/resume_check.py` (prints first unchecked step).
- **Step 3:** `docs/ARCHITECTURE.md` with an ASCII/Mermaid diagram of the services above **with deployment boundaries marked and justified** (scaling, failure isolation, independent release, resource profile). `docs/DESIGN_DECISIONS.md` skeleton (decisions + what was rejected).

### PHASE 1: Walking skeleton (priority: CRITICAL, this must work before anything else)
- **Step 4:** `contracts/classify_request.schema.json`, `contracts/classify_response.schema.json`, `docs/DATA_CONTRACT.md`; `src/common/models.py` (Pydantic models incl. `Route` enum, `Citation`, `HandoffPayload`, `RunStatus`).
- **Step 5:** `src/common/config.py` (env-only settings), `src/common/logging.py` (structured JSON logs with `correlation_id` / `run_id` contextvars), `src/common/db.py` (SQLAlchemy models + auto-create tables: `runs`, `run_steps`, `quarantine`, `feedback`, `index_freshness`, `eval_scores`, `cost_ledger`).
- **Step 6:** `src/api/validation.py` (schema/range/category/cross-field validation, field-level error list) + `tests/test_validation.py`.
- **Step 7:** `src/api/main.py` (FastAPI: `POST /v1/classify`, `GET /v1/runs/{id}`, `GET /healthz`, `GET /readyz`, `GET /metrics`), correlation-ID middleware, quarantine writer; `src/api/queue.py` (Celery or RQ task submit). Rejects quarantined and **no enqueue**.
- **Step 8:** `src/llm/provider.py` (abstract `LLMProvider`, `StubProvider`, `OpenAICompatProvider` with timeouts, token usage capture) and `src/llm_stub/app.py` (FastAPI stub with `STUB_DELAY_MS`, fixed JSON responses, mimics OpenAI-compatible `/v1/chat/completions` with usage counts).
- **Step 9:** `src/worker/tasks.py` with a **placeholder single-node "agent"** that returns a fixed, schema-valid result with route `specialist-classification-review` and basis "skeleton"; writes run + step rows. `docker/Dockerfile.api`, `docker/Dockerfile.worker`.
- **Step 10:** `docker-compose.yml` with `api`, `agent-worker`, `redis`, `postgres`, `llm-stub`, healthchecks, `depends_on` with health conditions, env from `.env`. `scripts/smoke.sh` that does `docker compose up -d --build`, waits for health, POSTs a valid request, polls until done, prints the result.
- **Step 11:** `web/index.html` + `web/app.js` (submit, poll, display recommendation, citations, escalation path) and `web` service (nginx) added to compose.
- **Step 12:** **Walking-skeleton gate:** run `scripts/smoke.sh` from a clean `docker compose down -v`; fix until green. Tick the gate in `PROGRESS.md` and tag `git tag skeleton-ok`. **Do not proceed past this step until it passes.**

### PHASE 2: Corpus and indexing (D2, L1)
- **Step 13:** `corpus/SOURCES.md` listing the official documents to download (CBIC Customs Tariff GRI; Chapters 73 and 96 with section and chapter notes; DGFT ITC-HS export policy for Chapters 73 and 96), with filename conventions, version/date fields and licence note; `scripts/download_corpus.sh` (best-effort; if network is unavailable print instructions to place PDFs in `corpus/raw/` manually). **Tell the user in chat which files to download if you cannot.** Do not invent corpus text.
- **Step 14:** `src/indexer/parse.py`: PDF text extraction (pdfplumber/pymupdf), detect scanned pages and OCR fallback (`ocrmypdf`/tesseract in the indexer image), normalized text + page numbers + doc version.
- **Step 15:** `src/indexer/chunk.py`: **structure-aware chunking** (document your strategy in `docs/CHUNKING_EMBEDDING.md` and tie it to the difficulty that some headings describe goods by material and others by what the article is):
  - one chunk per **heading** (4-digit) with its sub-headings, `kind=heading`, `heading_title` stored as separate field;
  - **notes as their own chunks** with `kind=section_note|chapter_note`, identifier like `Ch73/Note-1(a)`, and `applies_to` / `excludes_to` metadata extracted by regex (e.g., "does not cover", "excluded");
  - each GRI rule as its own chunk (`GRI-1`, `GRI-3(a)`...);
  - policy rows as `kind=policy` with HS code;
  - metadata on every chunk: `chunk_id, doc, doc_version, chapter, heading, kind, identifier, page, content_hash, embed_model, embed_model_version`.
  Plus build a **heading-title lexicon** (all heading titles across indexed chapters) for the `find_headings_naming_article` tool.
- **Step 16:** `src/indexer/embed_index.py` + `src/indexer/cli.py`: idempotent pipeline (`python -m indexer.cli build|reembed|status`): upsert by `chunk_id`; **re-embedding only chunks whose `content_hash` or `embed_model_version` changed** (no full rebuild); sentence-transformers `all-MiniLM-L6-v2` local; LangChain (or LlamaIndex) wrapper over Chroma; writes `index_freshness` (built_at, source doc versions, chunk count) and exposes metrics: `index_build_timestamp`, `index_chunks_total`, `index_pipeline_throughput_chunks_per_s`. `docker/Dockerfile.indexer`; add `chroma` and `indexer` to compose (indexer runs once, `restart: "no"`, api/worker wait for chroma healthy).
- **Step 17:** `tests/test_chunk.py`, `tests/test_indexer_idempotent.py` (second run changes 0 chunks; changing one chunk re-embeds only that one). Add `scripts/inspect_corpus.py` to print the passages the vacuum-flask case depends on (needed at Evaluation 1).

### PHASE 3: The agents (A1, A2, A3, F3 to F7)
- **Step 18:** `src/agent/tools.py`: implement the six tools above with per-call timeout, input validation, returned passages always carrying `chunk_id`, `identifier`, `text`; every tool call recorded to `run_steps` (tool, args, result ids, latency).
- **Step 19:** `prompts/` as **versioned artifacts**: `prompts/v1/*.md` and `prompts/v2/*.md` for entity extraction, planner, GRI application, verification; `src/agent/prompt_store.py` loads by `PROMPT_VERSION`; **the prompt version is stored with every response and every step**.
- **Step 20:** `src/agent/state.py` + `src/agent/graph.py`: LangGraph for Agent 1 with nodes `extract_entities → plan → tool_loop (agent chooses tools) → check_modifiers → requery_from_reading → apply_gri → propose → handoff`; **loop bounds** (steps, tool calls, wall-clock) enforced centrally; on limit exceeded → escalate, flagged `limit_exceeded`.
- **Step 21:** `src/agent/gri.py`: explicit GRI ordering helper/checklist (the agent must record which rule decided; tie after GRI 3 triggers escalation F7); `src/agent/entities.py` (article + materials extraction, structured output with schema validation and retry on invalid JSON).
- **Step 22:** `src/verifier/app.py` (FastAPI service, own tools, own prompt): **A3 verification**: (a) every citation `chunk_id`/`identifier` resolves to a passage in the retrieved set sent in the handoff (programmatic check), (b) claims supported by cited text (LLM check + string-overlap fallback), (c) GRI order respected. Returns `verified | needs_search(strategy) | escalate`. Route decision + `basis`. Add `Dockerfile.verifier` and compose entry.
- **Step 23:** Wire it all: `src/worker/tasks.py` replaces the placeholder: Agent 1 → handoff HTTP (timeout, retry) → verifier → if `needs_search` loop back to Agent 1 with a **different strategy** (bounded, e.g. max 2) → else final. **An unverified answer is never returned.** Worker-crash and verifier-down paths implemented per topology above. Update response contract (`route`, `basis`, `proposed_hs_code`, `rule_applied`, `citations[]`, `export_policy`, `escalation_path`, `prompt_version`, `degraded`, `cost`).
- **Step 24:** `tests/test_agent_flow.py` using the stub with scripted responses: valid request, out-of-corpus (escalates, no fabrication), tie (escalates), unsupported answer caught by verifier (re-search, then escalate), and the **section 4.1 vacuum-flask case** expected to find the heading that names vacuum flasks (record the passages and values in `eval/vacuum_flask_reference.md`; to be confirmed at Evaluation 1; verify against the real downloaded text, don't assume).

### PHASE 4: Guardrails and reliability (L4, A5)
- **Step 25:** `src/guardrails/injection.py`: prompt-injection defence on **every free-text field** (product_description, intended_use, any text echoed to a model): normalization (Unicode/zero-width/homoglyph), heuristic + pattern detector, spotlighting/delimiting of untrusted text in prompts, instruction-hierarchy system prompt, **tool-use hardening** (tool args from model validated; model cannot call tools with arguments outside allowed schema; untrusted text never placed in system role). Test suite with injection payloads.
- **Step 26:** `src/guardrails/output_filter.py`: schema-enforced output; the system can only emit a **"proposed classification"** with required disclaimer; block phrases/fields that issue a determination (e.g., "approved", "filed", "final classification", licence granted); strip unexpected URLs/markdown images; `src/guardrails/toxicity.py` (detoxify or keyword fallback) on input and output.
- **Step 27:** `src/common/resilience.py`: timeouts everywhere, `tenacity` bounded retry with exponential backoff + jitter, **circuit breaker** on the LLM provider (open/half-open/closed, metrics), **fallback path** documented in `docs/FALLBACK_PATH.md`: primary model → fallback model → (if breaker open) escalate with `degraded=true` and a clear message; **never confident when degraded**. Admin endpoint/env flag `CHAOS_PROVIDER_DOWN` to demo the breaker on request. `tests/test_resilience.py`.

### PHASE 5: Observability and reconstructability (D5, A6, L5)
- **Step 28:** OpenTelemetry tracing in api, worker, verifier (spans per agent step, tool call, LLM call; `run_id` and `correlation_id` attributes; propagate context across queue and HTTP) exported to Jaeger; add `jaeger` and optional `otel-collector` to compose.
- **Step 29:** Prometheus metrics in every service (`/metrics`): request count/latency histograms, error rate, per-agent task success, steps and tool calls per run, per-step latency, retry count, breaker state, queue depth, cache hits, tokens and cost counters; `observability/prometheus.yml`; container resource metrics via cAdvisor (add to compose) for per-container utilisation.
- **Step 30:** `src/common/cost.py`: token + cost recorded **at call time**, attributed per step and per run (prices from env); `cost_ledger` table; daily budget guard (`DAILY_BUDGET_USD`) that refuses new runs with 429/503 when exceeded.
- **Step 31:** `GET /v1/runs/{run_id}/trace`: **full reconstruction** of a run (every tool call, query, retrieved passage ids/text, prompt version, per-step latency and cost, verification outcome, route, degraded flags). `tests/test_trace_reconstruct.py`.
- **Step 32:** Grafana provisioning (`observability/grafana/provisioning/**` + dashboards JSON): p50/p95 latency, error rate, throughput, availability, per-container CPU/memory, **per-agent panels** (task success rate, steps and tool calls per run, end-to-end and per-step latency, retry rate, container uptime), index freshness, cost per run, quality over time (L6).

### PHASE 6: Caching, rate limiting, feedback (D7, L6)
- **Step 33:** `src/common/cache.py`: Redis caches for embeddings, retrievals, and whole runs (key = hash of normalized description + materials + prompt version + index version); TTLs; invalidated when index version changes; hit/miss metrics. Justify choices in `docs/DESIGN_DECISIONS.md`.
- **Step 34:** `src/api/ratelimit.py`: per-client token bucket in Redis (cost control), 429 with `Retry-After`, metrics; `tests/test_ratelimit.py`.
- **Step 35:** `POST /v1/runs/{id}/feedback` (`satisfactory: bool`, `reason: str`), persisted, `GET /v1/feedback/summary` aggregated; background scorer `src/eval/live_scorer.py` that samples live runs and scores them with the evaluation metrics, writing `eval_scores` for the quality-over-time chart.

### PHASE 7: Evaluation set and LLMOps (L2, L3)
- **Step 36:** `eval/scenarios.jsonl`: **>= 20 scenarios**, each with `id, request, expected_route, expected_hs_code (or null), expected_rule, supporting_passage_identifier, notes`. Must include: the vacuum-flask case; ordinary chapter 73 articles; ordinary chapter 96 articles; a case where a note excludes the obvious heading; an article-vs-material conflict; a tie that must escalate; out-of-chapter product (escalate); ambiguous description (seek clarification); injection attempts embedded in free text; a toxic input. **Passages must be identifiers that exist in the real indexed corpus**; where the corpus text isn't present yet, mark `status: needs_corpus_confirmation` and tell the user.
- **Step 37:** `src/eval/metrics.py`: **groundedness, context relevance, faithfulness, hallucination rate**, with computation stated in `docs/EVAL_METRICS.md`: e.g., groundedness = fraction of answer claims supported by retrieved passages (LLM judge, with deterministic overlap fallback in stub mode); context relevance = fraction of retrieved passages relevant to the query; faithfulness = fraction of citations that resolve and support the cited statement; hallucination rate = fraction of runs containing >= 1 unsupported claim or non-resolving citation. Integrate **TruLens** if installable, otherwise equivalent in-house implementation (state which).
- **Step 38:** `src/eval/run_eval.py` CLI (`python -m eval.run_eval --prompt-version v1 --out results/eval_v1.json`): batch runs the scenarios through the real pipeline (stub or real provider), outputs route accuracy, code accuracy, escalation precision/recall, the four metrics, cost and latency.
- **Step 39:** **Prompt comparison (L2):** run v1 vs v2 on the same set; `src/eval/compare.py` emits `results/prompt_comparison.md` (which was better, on which metric, by how much). **Deliberate change experiment (L3):** make ONE deliberate change (e.g., enable the "re-query from what was read" step, or add the `list_notes_for` tool), report all four metrics before and after in `results/deliberate_change.md`. Real numbers only; if run only in stub mode, say so clearly.

### PHASE 8: Load, SLO, scaling (D6, A7)
- **Step 40:** **BEFORE ANY LOAD MEASUREMENT:** write `docs/SLO.md` declaring the end-to-end p95 target (submission to final result), justified against the business context (a trade analyst waiting during classification; held consignments), with the stub delay assumption (`STUB_DELAY_MS` per LLM call, calls per run). **Commit this file immediately in its own commit** (`git commit -m "SLO declared before measurement"`), so the timestamp proves it preceded the results. Never edit the target afterwards.
- **Step 41:** `loadtest/locustfile.py` (submit then poll until done; measures **submission to final result**, not just submit latency) + `docker-compose.loadtest.yml` or profile that points the worker at `llm-stub`; `scripts/run_load.sh` sweeps concurrency (e.g. 5, 10, 20, 50, 100) and writes `results/load_*.csv`.
- **Step 42:** Scaling experiment: run with `docker compose up --scale agent-worker=1` vs `=3`; record RPS, p50, p95; `docs/LOAD_RESULTS.md`: whether the SLO was met, **the concurrency at which it fails and the responsible component**, effect of scaling, and if scaling does not help, the real bottleneck (Redis, Postgres, verifier, Chroma, API) identified from metrics. Also measure effect of caching on p95 and cost per run, and cost per 100 runs with the largest cost driver (L5) in `docs/COST_REPORT.md`.

### PHASE 9: Docs, runbook, demo (D8, deliverables)
- **Step 43:** `docs/RUNBOOK.md`: two most likely failure modes (e.g. LLM provider unavailable / rate-limited; Chroma or index stale/empty) each with **symptom, confirmation (exact commands/dashboards), recovery**. `docs/INCIDENT_LOG.md`: **only genuine incidents that really happened** during development (copy from what you logged in earlier steps; if none yet, leave the template and tell the user to record a real one).
- **Step 44:** `scripts/demo/` one script per demo item: (1) clean-clone `docker compose up`, (2) valid request with citations, (3) trace one run (Jaeger link + `/trace`), (4) malformed request quarantined with proof that queue/run count unchanged, (5) unanswerable case escalates, (6) verifier catching unsupported answer (inject via a test flag), (7) prompt injection and guardrail response, (8) breaker opens with provider down and degraded path, (9) Locust results + `--scale`, (10) section 4.1 vacuum-flask case. `docs/DEMO_CHECKLIST.md` listing the 10 items with the command for each.
- **Step 45:** `README.md` final: sufficient for a stranger to run the system unassisted (prereqs, copy `.env.example`, set free-tier provider variables, download corpus, `docker compose up`, run indexer, smoke test, open web client/Grafana/Jaeger, run eval, run load test, repo map). `docs/REPORT.md`: problem and scope; agent design (topology, tools, verification, loop limits); architecture diagram with boundaries; design decisions and rejected alternatives; evaluation before/after; p95 target, measured results, bottleneck, cost per 100 runs; **what did not work**.
- **Step 46:** **Final QA:** (a) from a clean clone (`git clone` into a temp dir, copy `.env.example` to `.env`) run `docker compose up --build` and `scripts/smoke.sh`; (b) `pytest -q`; (c) grep the repo for secrets, URLs of providers, model identifiers (D4 violation check); (d) confirm `docker compose up --scale agent-worker=3` works; (e) update `PROGRESS.md` and `docs/PRIORITIES.md` (built / deferred / why); write `SUBMISSION.md` mapping each of the 22 requirements (F1 to F8, A1 to A8, L1 to L6, D1 to D8) to its file/evidence or "deferred: reason".

---

## ACCEPTANCE CRITERIA (verify before declaring done)
- [ ] Clean clone, `docker compose up`, valid request returns a routed recommendation with citations that resolve to retrieved text.
- [ ] Malformed request is rejected and quarantined, and no run starts.
- [ ] Out-of-corpus and tie cases escalate; no fabricated answers; unverified answers are never returned.
- [ ] Section 4.1 vacuum-flask case: finds the heading naming vacuum flasks, applies GRI in order, cites rule and heading.
- [ ] Two real agents (separate services) with documented topology and failure handling.
- [ ] Guardrails (injection, output filter, toxicity), timeouts, retry, circuit breaker and fallback demonstrable.
- [ ] Traces, metrics, structured logs and Grafana dashboard; any run fully reconstructible by run id.
- [ ] >= 20-scenario eval set, 4 metrics, prompt-variant comparison, before/after of one deliberate change.
- [ ] SLO committed before load test; Locust results, failing concurrency, `--scale` effect, cost per 100 runs reported.
- [ ] README, runbook, genuine incident log, `.env.example`, eval set all present; no secrets or model IDs in the repo.

## FIRST ACTION
Read `PROGRESS.md` and `STATE.md` if present. If neither exists, begin at Step 1 now. Do not ask clarifying questions; make reasonable choices, record them in `STATE.md`, and proceed. Remember: the walking skeleton (Steps 4 to 12) comes first.

========================= END OF PROMPT =========================


## RESUME PROMPT (paste this into a fresh session after your tokens renew)

```
Continue the project in this repo (export-classification-service).
1. Read PROGRESS.md and STATE.md.
2. Run `python scripts/resume_check.py` to find the first unchecked step.
3. If Phase 1 is complete, run `scripts/smoke.sh` (or `pytest -q`) to confirm the last finished step still works; fix it first if not.
4. Continue from that step, following the working rules in MASTER_PROMPT_mp07_export_classification.md
   (1 to 3 files per step, complete and runnable files, update PROGRESS.md and STATE.md, commit after every step,
   print only a one-line status after each step).
Do not redo completed steps and do not rewrite existing files unless a test fails.
Never invent corpus text, incidents, or measurements.
```