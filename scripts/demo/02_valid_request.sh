#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import json, urllib.request, uuid
body={"client_request_id":str(uuid.uuid4()),"product_description":"Stainless steel vacuum flask for carrying hot drinks","materials":["stainless_steel"],"destination_country":"US","client_id":"demo-client"}
req=urllib.request.Request('http://localhost:8000/v1/classify',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
print(urllib.request.urlopen(req).read().decode())
PY
