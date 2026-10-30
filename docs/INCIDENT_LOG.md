# Incident log

## 2026-10-29 14:38:23 UTC — Ruff installation unavailable in build workspace

- **Step/command:** optional local lint setup; `python -m pip install --quiet ruff==0.8.4`.
- **Symptom:** pip retries failed with `Temporary failure in name resolution`, then reported no matching distribution because the package index could not be reached.
- **Cause:** this workspace could not resolve/access the package index during this build; Ruff was not preinstalled.
- **Fix / mitigation:** Ruff was not installed locally. Syntax compilation and the pytest suite were run instead; `.env`-backed `make lint` installs/runs Ruff inside the project container on a Docker host. Lint remains unverified here.
- **Verification:** `python -m compileall -q src tests scripts loadtest` and `pytest -q` passed. No code failure is attributed to Ruff.

## 2026-10-30 — Docker engine unavailable for Compose smoke gate

- **Step/command:** Phase B setup; `docker compose down -v --remove-orphans` and `bash scripts/smoke.sh`.
- **Symptom:** Docker CLI and Compose were installed, but the client could not connect to the `desktop-linux` engine named pipe. The Windows `bash` command resolved to WSL, which has no installed distribution.
- **Cause:** Docker Desktop's Linux engine was not running in this workspace; WSL was not configured for running the smoke script.
- **Fix / mitigation:** Created the ignored local `.env` with a private password, validated `docker compose config -q`, and identified `C:\Program Files\Git\bin\bash.exe` as an available script runner. The Compose smoke gate remains unverified until the Docker engine is started.
- **Verification:** `docker info` reported the missing `dockerDesktopLinuxEngine` pipe; `docker compose config -q` passed. Raw command output is retained in `verification/logs/B_preclean.txt` and `verification/logs/B_smoke.txt`.

## 2026-10-30 — Web healthcheck resolved localhost to IPv6

- **Step/command:** Phase B scale verification; `docker compose ps` and the web healthcheck.
- **Symptom:** The web container served the host endpoint successfully, but its healthcheck repeatedly failed with `wget: can't connect to remote host: Connection refused` while probing `localhost`.
- **Cause:** Alpine resolved `localhost` to `::1`, while nginx was listening on IPv4.
- **Fix:** Changed the Compose healthcheck URL to `http://127.0.0.1/healthz`.
- **Verification:** Recreated the web service; `docker compose ps` reported `healthy`, and an in-container probe returned `ok`. Evidence is in `verification/logs/B_scale3_fixed.txt` and `verification/logs/B_web_health_fixed.txt`.

## 2026-10-30 — Container test invocation shared live Redis queue

- **Step/command:** Phase C; initial `docker compose run ... api pytest -q` while the scaled worker stack was running.
- **Symptom:** `tests/test_api.py::test_submit_returns_202_and_run_id` observed queue length `0` instead of `1`.
- **Cause:** The test container inherited the Compose Redis URL, and a live worker consumed the test item before the assertion.
- **Fix / mitigation:** Stopped the application stack and reran the test with an unreachable Redis URL to force the documented in-memory test fallback; no source change was needed.
- **Verification:** Isolated container pytest passed all 24 tests; evidence is in `verification/logs/C_pytest_container_clean.txt`.
