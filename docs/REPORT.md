# Mini Project 07 — Export Classification Check Service

## Problem and scope

The service accepts a structured product description, performs evidence retrieval against official Customs Tariff / GRI and DGFT export-policy passages, returns a proposal and review route, and never files a declaration. Only tariff Chapters 73 and 96 are in scope. Final decisions remain with a licensed customs broker.

## Agent design

The API validates and quarantines before queue submission. Agent 1 extracts request fields and searches indexed heading/title, GRI, note and policy passages using bounded lexical tools. It hands off a typed payload plus passage IDs to a separate verifier. The verifier resolves citation IDs against the exact handoff and checks route/evidence invariants. Unknown evidence, missing policy support, suspected injection, an out-of-scope hint, tool-limit breach or verifier failure leads to specialist review, not a fabricated HS code.

## Architecture and boundaries

See `docs/ARCHITECTURE.md`. API, worker, verifier, queue, database, static web and LLM stub have separate container boundaries. Chroma and observability services are optional profiles. The current graph is deterministic; full LangGraph model-selected tools and full Chroma semantic retrieval are not implemented.

## Evaluation and performance

No actual corpus-backed evaluation, prompt-comparison experiment, load measurement, scaling result or cost benchmark is provided because these require the source corpus and Docker runtime. The SLO is declared in `docs/SLO.md` before load measurements. Use `src/eval/run_eval.py` and `scripts/run_load.sh` to generate real result files; do not treat `needs_corpus_confirmation` examples as a gold set.

## What is incomplete

- The current official PDFs and document versions/effective dates have not been bundled/indexed.
- OCR execution and structure extraction need manual validation against actual PDFs.
- Semantic embeddings/Chroma integration and fully dynamic LangGraph tool selection remain deferred.
- Retry/breaker helpers, token cost/budget accounting, OTEL tracing, full metrics/dashboards, feedback live scoring, and scaling measurements are partial/deferred.
- The Compose walking-skeleton gate is not verified in this environment because Docker is unavailable.

No performance numbers or official tariff language have been fabricated in this report.
