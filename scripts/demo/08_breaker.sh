#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
from src.common.resilience import CircuitBreaker
breaker=CircuitBreaker(threshold=1,reset_s=60)
try: breaker.call(lambda: (_ for _ in ()).throw(RuntimeError('simulated demo failure')))
except RuntimeError: pass
print('breaker state after one controlled test failure:', breaker.state)
assert breaker.state == 'open'
PY
