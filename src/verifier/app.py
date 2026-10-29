"""Independent verifier API: validate citations and conservative route semantics."""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from src.common.models import HandoffPayload, Route

app = FastAPI(title="Export classification verifier", version="0.1.0")


class VerifyResponse(BaseModel):
    verified: bool
    outcome: str
    basis: str
    unresolved_citations: list[str]


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/verify", response_model=VerifyResponse)
def verify(payload: HandoffPayload) -> VerifyResponse:
    """Check citation references against handoff passages and suppress unsafe claims."""
    by_id = {str(p.get("chunk_id")): p for p in payload.passages if p.get("chunk_id")}
    unresolved = []
    for citation in payload.citations:
        passage = by_id.get(citation.chunk_id)
        if not passage or str(passage.get("identifier", "")) != citation.identifier:
            unresolved.append(citation.chunk_id)
            continue
        passage_text = str(passage.get("text", "")).lower()
        excerpt = citation.excerpt.strip().lower()
        if excerpt and excerpt[:min(24, len(excerpt))] not in passage_text:
            unresolved.append(citation.chunk_id)
    if unresolved:
        return VerifyResponse(verified=False, outcome="escalate", basis="Citation did not resolve exactly to the handed-off passage.", unresolved_citations=unresolved)
    if payload.route != Route.CLEAR_FOR_FILING and payload.proposed_hs_code is None:
        return VerifyResponse(verified=True, outcome="verified", basis="Conservative escalation contains no asserted HS code.", unresolved_citations=[])
    if payload.route == Route.CLEAR_FOR_FILING and (not payload.citations or not payload.rule_applied or not payload.proposed_hs_code):
        return VerifyResponse(verified=False, outcome="escalate", basis="Clearance route is missing mandatory source evidence.", unresolved_citations=[])
    return VerifyResponse(verified=True, outcome="verified", basis="Citation references resolved; final human review remains required.", unresolved_citations=[])
