#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f docs/SLO.md ]]; then echo "Declare the SLO before any load test." >&2; exit 2; fi
if [[ ! -f .env ]]; then cp .env.example .env; fi
docker compose --profile loadtest up -d --build api agent-worker verifier postgres redis
for users in 5 10 20 50 100; do
  echo "Running end-to-end load at ${users} concurrent users"
  docker compose --profile loadtest run --build --rm -e LOAD_USERS="$users" loadtest \
    --headless -H http://api:8000 --users "$users" --spawn-rate 2 --run-time 60s \
    --csv "/app/results/load_${users}" --only-summary
done
echo "CSV outputs saved under results/. Inspect p95 from the submit-to-terminal-result E2E event and record the real runs in docs/LOAD_RESULTS.md."
