#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import json,urllib.request
payload={"run_id":"demo-unresolved","request":{},"route":"specialist-classification-review","basis":"review","passages":[],"citations":[{"chunk_id":"missing","identifier":"GRI-1","doc":"unavailable.pdf","excerpt":"unsupported citation sample"}]}
req=urllib.request.Request('http://localhost:8002/verify',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
print(urllib.request.urlopen(req).read().decode())
PY
