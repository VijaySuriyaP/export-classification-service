"""Compare two generated evaluation JSON files without inventing measurements."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

METRICS = ("route_accuracy", "groundedness", "context_relevance", "faithfulness", "hallucination_rate")


def main() -> None:
    """Write a metric-by-metric comparison only when result files exist."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--v1", default="results/eval_v1.json")
    parser.add_argument("--v2", default="results/eval_v2.json")
    parser.add_argument("--out", default="results/prompt_comparison.md")
    args = parser.parse_args()
    a_path, b_path = Path(args.v1), Path(args.v2)
    if not a_path.exists() or not b_path.exists():
        raise SystemExit("Both evaluation result files must exist; run each prompt variant first.")
    a, b = json.loads(a_path.read_text()), json.loads(b_path.read_text())
    lines = ["# Prompt comparison", "", "Actual generated result files compared; interpretation depends on corpus/gold-label readiness.", "", "| Metric | v1 | v2 | v2 - v1 |", "|---|---:|---:|---:|"]
    for metric in METRICS:
        va, vb = a.get("summary", {}).get(metric), b.get("summary", {}).get(metric)
        delta = f"{vb - va:+.4f}" if isinstance(va, (int, float)) and isinstance(vb, (int, float)) else "not available"
        lines.append(f"| {metric} | {va if va is not None else 'not available'} | {vb if vb is not None else 'not available'} | {delta} |")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
