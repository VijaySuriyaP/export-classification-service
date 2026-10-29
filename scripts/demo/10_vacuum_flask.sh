#!/usr/bin/env bash
set -euo pipefail
docker compose exec -T agent-worker python scripts/inspect_corpus.py
echo "Manual confirmation against the current official PDFs is required; see eval/vacuum_flask_reference.md."
