"""Run the scenario file against the live asynchronous API and save actual results."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import httpx

from src.eval.metrics import evaluation_summary

ROOT = Path(__file__).resolve().parents[2]


def run_scenario(base_url: str, scenario: dict[str, Any], prompt_version: str) -> dict[str, Any]:
    """Submit one scenario and poll until a terminal run state or timeout."""
    request_body = scenario["request"]
    start = time.monotonic()
    try:
        with httpx.Client(timeout=5) as client:
            response = client.post(f"{base_url}/v1/classify", json=request_body, headers={"x-eval-prompt-version": prompt_version})
            response.raise_for_status()
            run_id = response.json()["run_id"]
            deadline = time.monotonic() + 90
            result: dict[str, Any] = {}
            while time.monotonic() < deadline:
                polled = client.get(f"{base_url}/v1/runs/{run_id}")
                polled.raise_for_status()
                result = polled.json()
                if result.get("status") in {"completed", "failed_escalated"}:
                    break
                time.sleep(0.25)
            return {"id": scenario["id"], "route": result.get("route"), "basis": result.get("basis", ""),
                "citations": result.get("citations", []), "citations_resolved": all(c.get("chunk_id") for c in result.get("citations", [])),
                "evidence_text": " ".join(c.get("excerpt", "") for c in result.get("citations", [])),
                "unsupported_claim": bool(result.get("proposed_hs_code") and not result.get("citations")),
                "expected_route": scenario.get("expected_route"), "expected_hs_code": scenario.get("expected_hs_code"),
                "status": result.get("status"), "elapsed_s": round(time.monotonic() - start, 3),
                "corpus_status": scenario.get("status", "needs_corpus_confirmation")}
    except Exception as exc:
        return {"id": scenario.get("id"), "status": "request_failed", "error_type": type(exc).__name__,
            "elapsed_s": round(time.monotonic() - start, 3), "corpus_status": scenario.get("status", "needs_corpus_confirmation")}


def main() -> None:
    """Evaluate all configured scenarios and write the actual result JSON."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-version", default="v1")
    parser.add_argument("--out", default="results/eval.json")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    scenario_path = ROOT / "eval" / "scenarios.jsonl"
    scenarios = [json.loads(line) for line in scenario_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [run_scenario(args.base_url, scenario, args.prompt_version) for scenario in scenarios]
    summary = evaluation_summary(rows)
    output = {"prompt_version": args.prompt_version, "run_mode": "live API; provider mode determined by deployment env",
        "summary": summary, "results": rows}
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
