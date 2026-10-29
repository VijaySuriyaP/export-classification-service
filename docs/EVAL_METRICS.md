# Evaluation metrics

The current in-house deterministic implementation is used instead of TruLens. It provides a reproducible baseline for offline/stub tests, not a replacement for expert-reviewed evaluation.

- **Groundedness:** fraction of non-empty output claims sharing at least one token with cited/retrieved passage text. The simple lexical overlap fallback is intentionally transparent and may overestimate support.
- **Context relevance:** relevant passages divided by retrieved passages; current `run_eval` uses presence of citation evidence as a coarse indicator, not a human gold label.
- **Faithfulness:** citations that resolve to handed-off source identifiers divided by citations evaluated.
- **Hallucination rate:** runs with an unsupported claim or a citation that does not resolve divided by evaluated runs.
- **Route accuracy:** only interpreted when the scenario's gold route is confirmed. All provided scenario records are marked `needs_corpus_confirmation`, so generated results must be described with this caveat.

No evaluation values are asserted in this document. `src/eval/run_eval.py` writes actual output to a result file when run against a live service.
