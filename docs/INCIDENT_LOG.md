# Incident log

## 2026-10-29 14:38:23 UTC — Ruff installation unavailable in build workspace

- **Step/command:** optional local lint setup; `python -m pip install --quiet ruff==0.8.4`.
- **Symptom:** pip retries failed with `Temporary failure in name resolution`, then reported no matching distribution because the package index could not be reached.
- **Cause:** this workspace could not resolve/access the package index during this build; Ruff was not preinstalled.
- **Fix / mitigation:** Ruff was not installed locally. Syntax compilation and the pytest suite were run instead; `.env`-backed `make lint` installs/runs Ruff inside the project container on a Docker host. Lint remains unverified here.
- **Verification:** `python -m compileall -q src tests scripts loadtest` and `pytest -q` passed. No code failure is attributed to Ruff.
