# Load and scaling results

**Status: NOT MEASURED.** Docker/Compose is unavailable in the current build environment. No RPS, p50, p95, failing-concurrency point, scale comparison or bottleneck is claimed.

After Docker is available:

1. Keep `docs/SLO.md` unchanged.
2. Run `bash scripts/run_load.sh` from a clean stack.
3. Run once with one worker and once with three workers. Save all generated CSV files under `results/` and record the exact commands, date, image revision and environment here.
4. Inspect PostgreSQL, Redis, API metrics and worker logs before naming a bottleneck. Do not attribute bottlenecks without evidence.
