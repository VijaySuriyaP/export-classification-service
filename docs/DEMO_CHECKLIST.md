# Demo checklist

Run from repository root after Docker Compose is available. Do not claim any Docker-only item passed until you actually ran it.

1. Clean walking skeleton: `bash scripts/demo/01_walking_skeleton.sh`
2. Submit valid request and inspect citations: `bash scripts/demo/02_valid_request.sh`
3. Reconstruct trace: `bash scripts/demo/03_trace.sh`
4. Malformed request quarantined without enqueue: `bash scripts/demo/04_quarantine.sh`
5. Unanswerable input escalates: `bash scripts/demo/05_unanswerable.sh`
6. Verifier catches unresolved citation: `bash scripts/demo/06_verifier.sh`
7. Prompt injection is escalated: `bash scripts/demo/07_injection.sh`
8. Provider breaker helper unit demonstration: `bash scripts/demo/08_breaker.sh`
9. Load/concurrency run: `bash scripts/demo/09_load.sh` (Docker/loadtest profile required)
10. Vacuum-flask passage audit: `bash scripts/demo/10_vacuum_flask.sh` (requires current official corpus and human confirmation)

A clean default profile deliberately escalates without asserting an HS code if no official passages have been indexed.
