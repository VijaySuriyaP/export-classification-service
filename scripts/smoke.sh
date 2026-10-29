#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f .env ]]; then cp .env.example .env; fi
docker compose up -d --build
printf 'Waiting for API readiness'
for _ in $(seq 1 60); do
  if docker compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=2)" >/dev/null 2>&1; then
    echo ' ready'; break
  fi
  printf '.'
  sleep 2
done
# Smoke request is executed from inside the API container: host needs Docker only.
docker compose exec -T api python - <<'PY'
import json, time, urllib.error, urllib.request, uuid
base = 'http://127.0.0.1:8000'
payload = {
    'client_request_id': str(uuid.uuid4()),
    'product_description': 'Stainless steel vacuum flask for carrying hot drinks',
    'materials': ['stainless_steel'],
    'intended_use': 'Reusable drink container',
    'destination_country': 'US',
    'client_id': 'smoke-test',
}
request = urllib.request.Request(base + '/v1/classify', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'}, method='POST')
with urllib.request.urlopen(request, timeout=10) as response:
    assert response.status == 202, response.status
    submitted = json.load(response)
run_id = submitted['run_id']
print('submitted:', json.dumps(submitted))
for _ in range(120):
    with urllib.request.urlopen(base + '/v1/runs/' + run_id, timeout=10) as response:
        result = json.load(response)
    if result.get('status') in {'completed', 'failed_escalated'}:
        print('terminal result:', json.dumps(result, indent=2))
        assert result.get('route') in {'clear-for-filing', 'seek-product-clarification', 'specialist-classification-review'}
        assert result.get('disclaimer')
        break
    time.sleep(0.5)
else:
    raise SystemExit('poll timeout')
PY
