"""Worker orchestration for Agent 1, independent verifier and durable trace."""
from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx
from sqlalchemy import select

from src.agent.graph import classify_request
from src.common.db import RunRecord, RunStep, SessionLocal, init_db
from src.common.models import HandoffPayload, Route
from src.guardrails.output_filter import DISCLAIMER, filter_result

logger = logging.getLogger(__name__)


def _save_step(session, run_id: str, name: str, detail: dict[str, Any], started: float) -> None:
    session.add(RunStep(run_id=run_id, step_name=name, detail=detail,
        latency_ms=round((time.monotonic() - started) * 1000, 3), prompt_version=os.getenv("PROMPT_VERSION", "v1")))


def execute_run(run_id: str) -> dict[str, Any] | None:
    """Process one queued run and persist a response that passed verification."""
    init_db()
    with SessionLocal() as session:
        record = session.get(RunRecord, run_id)
        if record is None:
            logger.warning("queued run missing from database: %s", run_id)
            return None
        record.status = "running"
        session.commit()
        started = time.monotonic()
        try:
            handoff = classify_request(run_id, record.request_data)
            _save_step(session, run_id, "agent1_handoff", {"route": handoff.route.value, "citation_count": len(handoff.citations), "trace": handoff.trace}, started)
            verified: dict[str, Any]
            verifier_url = os.getenv("VERIFIER_URL", "")
            if verifier_url:
                try:
                    response = httpx.post(f"{verifier_url.rstrip('/')}/verify", json=handoff.model_dump(mode="json"), timeout=5.0)
                    response.raise_for_status()
                    verified = response.json()
                except Exception as exc:
                    handoff = HandoffPayload(run_id=run_id, request=record.request_data,
                        route=Route.SPECIALIST_CLASSIFICATION_REVIEW,
                        basis="Verifier unavailable after bounded hand-off attempt; confidence suppressed.",
                        prompt_version=os.getenv("PROMPT_VERSION", "v1"), degraded=True,
                        passages=handoff.passages, trace=handoff.trace + [{"step": "verifier_failure", "detail": type(exc).__name__}])
                    verified = {"verified": True, "outcome": "degraded_escalation", "basis": handoff.basis}
            else:
                # Local unit tests run the verifier logic directly via the service test suite.
                verified = {"verified": not (handoff.route == Route.CLEAR_FOR_FILING), "outcome": "escalate", "basis": "No verifier URL configured; clearance is disabled."}
            _save_step(session, run_id, "verification", verified, started)
            if not verified.get("verified") or verified.get("outcome") in {"needs_search", "escalate"}:
                handoff.route = Route.SPECIALIST_CLASSIFICATION_REVIEW
                handoff.proposed_hs_code = None
                handoff.rule_applied = None
                handoff.export_policy = None
                handoff.basis = "Independent verification did not approve the proposed evidence; specialist review required."
            result = {
                "run_id": run_id, "status": "completed", "route": handoff.route.value,
                "basis": handoff.basis, "proposed_hs_code": handoff.proposed_hs_code,
                "rule_applied": handoff.rule_applied, "citations": [c.model_dump(mode="json") for c in handoff.citations],
                "export_policy": handoff.export_policy,
                "escalation_path": ["licensed-customs-broker"] if handoff.route != Route.CLEAR_FOR_FILING else [],
                "prompt_version": handoff.prompt_version, "degraded": handoff.degraded,
                "trace": handoff.trace, "verification": verified, "disclaimer": DISCLAIMER,
            }
            result = filter_result(result)
            record.status = "completed"
            record.result = result
            record.updated_at = record.updated_at
            session.commit()
            return result
        except Exception as exc:
            logger.exception("run failed and will be escalated")
            result = filter_result({"run_id": run_id, "status": "failed_escalated",
                "route": Route.SPECIALIST_CLASSIFICATION_REVIEW.value,
                "basis": "Processing failed; no classification is asserted. Specialist review required.",
                "proposed_hs_code": None, "rule_applied": None, "citations": [], "export_policy": None,
                "escalation_path": ["licensed-customs-broker"], "prompt_version": os.getenv("PROMPT_VERSION", "v1"),
                "degraded": True, "error_type": type(exc).__name__})
            record.status = "failed_escalated"
            record.error = type(exc).__name__
            record.result = result
            session.commit()
            return result
