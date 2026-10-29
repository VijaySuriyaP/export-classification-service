#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import json, urllib.error, urllib.request
base='http://localhost:8000'
def get(path): return json.loads(urllib.request.urlopen(base+path).read())
try:
    req=urllib.request.Request(base+'/v1/classify',data=json.dumps({"product_description":"x"}).encode(),headers={'Content-Type':'application/json'},method='POST')
    urllib.request.urlopen(req)
except urllib.error.HTTPError as exc:
    print('malformed status:', exc.code, exc.read().decode())
    assert exc.code == 422
print('Queue length is not exposed publicly. Verify quarantine and no-run invariant with: pytest -q tests/test_api.py::test_invalid_request_is_quarantined_without_enqueue')
PY
