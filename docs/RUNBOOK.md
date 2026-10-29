# Runbook

## 1. Provider unavailable or rate-limited

**Symptoms:** a configured compatible-provider call throws, or the worker creates a degraded specialist-review run.

**Confirm:** `docker compose logs agent-worker verifier`; inspect `GET /v1/runs/{run_id}` and `GET /v1/runs/{run_id}/trace`.

**Recover:** switch `LLM_PROVIDER=stub` and `LLM_DRY_RUN=true` in `.env` for offline operation, then `docker compose up -d --build`. The present deterministic graph does not require a provider call; any unintegrated provider failure should not be described as the cause of a result unless the logs show it.

## 2. Corpus missing, stale or not searchable

**Symptoms:** the run says that official documents are not indexed, or `corpus/processed/index_status.json` reports zero chunks.

**Confirm:** `find corpus/raw -maxdepth 1 -type f -name '*.pdf'`; `python -m src.indexer.cli status`; `python scripts/inspect_corpus.py`.

**Recover:** follow `corpus/SOURCES.md` to download the current official Customs Tariff First Schedule/GRI and current DGFT Schedule-II export policy. Put PDFs in `corpus/raw/`, record version/effective date in the source register, run `make index`, then verify real source passages manually. Never put fixture data into the live index.

## Useful runtime commands

- `docker compose ps`
- `docker compose logs -f api agent-worker verifier`
- `curl http://localhost:8000/readyz`
- `curl http://localhost:8000/metrics`
- `curl http://localhost:8000/v1/runs/<run-id>/trace`
