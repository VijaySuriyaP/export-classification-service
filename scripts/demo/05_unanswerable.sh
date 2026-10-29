#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import json,urllib.request,uuid,time
base='http://localhost:8000'; body={"client_request_id":str(uuid.uuid4()),"product_description":"Fresh bananas intended for retail grocery sale","materials":["other"],"destination_country":"US","client_id":"demo-unanswerable"}
req=urllib.request.Request(base+'/v1/classify',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST'); run= json.loads(urllib.request.urlopen(req).read())['run_id']
for _ in range(120):
 data=json.loads(urllib.request.urlopen(base+'/v1/runs/'+run).read())
 if data.get('status') in ('completed','failed_escalated'): print(json.dumps(data,indent=2)); assert data.get('proposed_hs_code') is None; break
 time.sleep(.25)
PY
