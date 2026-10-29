#!/usr/bin/env bash
set -euo pipefail
if [[ -z "${RUN_ID:-}" ]]; then echo "Set RUN_ID to a run ID from demo 02." >&2; exit 2; fi
python -c 'import os,urllib.request; print(urllib.request.urlopen("http://localhost:8000/v1/runs/"+os.environ["RUN_ID"]+"/trace").read().decode())'
echo "Optional Jaeger UI (only if observability profile is running): http://localhost:16686"
