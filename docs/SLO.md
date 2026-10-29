# Service-level objective (declared before load testing)

**Target:** end-to-end p95 submission-to-terminal-result latency is **60 seconds or less** for the offline stub profile, measured from the caller's POST start until the polling endpoint returns `completed` or `failed_escalated`.

**Rationale:** an export analyst should be able to obtain a review route within roughly a minute in a demo-scale workflow; a held consignment makes indefinite waiting undesirable. A production SLO must be revisited using the organization's true business process, corpus size, concurrency, network and licensed-provider latency.

**Stub assumption:** `STUB_DELAY_MS` defaults to `0`. The currently implemented deterministic evidence-first classification path makes **zero LLM chat-completion calls per run**, so the expected stub model-delay contribution is zero in this version. The standalone stub service supports an adjustable delay for provider-adapter demos. If future agent iterations call the stub, record the actual calls-per-run and delay before interpreting load results.

This target was set before any load measurements. No load tests or performance measurements were run when this file was created. Do not edit the target after measuring; record the actual result and any mismatch in `docs/LOAD_RESULTS.md`.
