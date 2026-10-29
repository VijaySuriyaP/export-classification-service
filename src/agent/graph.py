"""Bounded evidence-first Agent 1 workflow; no tariff claims without official passages."""
from __future__ import annotations

import os
import time
from typing import Any

from src.agent.entities import extract_entities
from src.agent.gri import GRI_ORDER
from src.agent.tools import AgentTools
from src.common.models import Citation, HandoffPayload, Route
from src.guardrails.injection import detect_prompt_injection
from src.guardrails.toxicity import is_toxic


def classify_request(run_id: str, request: dict[str, Any]) -> HandoffPayload:
    """Run bounded retrieval and return a typed evidence handoff for verification."""
    workflow_started = time.monotonic()
    entities = extract_entities(request)
    tools = AgentTools(request)
    prompt_version = os.getenv("PROMPT_VERSION", "v1")
    description = str(request.get("product_description", ""))
    combined_text = description + " " + str(request.get("intended_use") or "")
    trace: list[dict[str, Any]] = []
    injection = detect_prompt_injection(combined_text)
    if injection["detected"]:
        return HandoffPayload(run_id=run_id, request=request, route=Route.SPECIALIST_CLASSIFICATION_REVIEW,
            basis="Potential prompt injection detected in untrusted product text; no automated classification asserted.",
            prompt_version=prompt_version, trace=[{"step": "guardrail_injection", "detail": injection}])
    if is_toxic(combined_text):
        return HandoffPayload(run_id=run_id, request=request, route=Route.SPECIALIST_CLASSIFICATION_REVIEW,
            basis="Input failed the safety text screen; specialist review required.", prompt_version=prompt_version,
            trace=[{"step": "guardrail_toxicity", "detail": {"blocked": True}}])
    if len(set(entities["words"])) <= 2 or any(term in combined_text.lower() for term in ("something metal", "some item", "product item", "thing for use")):
        return HandoffPayload(run_id=run_id, request=request, route=Route.SEEK_PRODUCT_CLARIFICATION,
            basis="The description does not identify the article precisely enough to compare tariff headings.", prompt_version=prompt_version)
    hint_chapter = entities.get("hs_hint_chapter")
    if hint_chapter and hint_chapter not in {"73", "96"}:
        return HandoffPayload(run_id=run_id, request=request, route=Route.SPECIALIST_CLASSIFICATION_REVIEW,
            basis="The supplied HS hint is outside the supported Chapters 73 and 96 corpus; no classification asserted.", prompt_version=prompt_version)

    max_steps = int(os.getenv("MAX_STEPS", "8"))
    max_calls = int(os.getenv("MAX_TOOL_CALLS", "16"))
    searches = tools.corpus_search(description + " " + " ".join(entities["materials"]), limit=8)
    headings = tools.find_headings_naming_article(description, limit=8)
    trace.extend([{"step": "extract_entities", "detail": {"materials": entities["materials"], "word_count": len(entities["words"])}},
                  {"step": "retrieve", "detail": {"search_hits": len(searches), "heading_hits": len(headings)}}])
    retrieved = {x["chunk_id"]: x for x in (searches + headings)}
    candidates = sorted(retrieved.values(), key=lambda x: float(x.get("retrieval_score", 0)), reverse=True)
    wall_clock_limit = int(os.getenv("MAX_WALL_CLOCK_S", "30"))
    if len(trace) > max_steps or tools.call_count > max_calls or time.monotonic() - workflow_started > wall_clock_limit:
        return HandoffPayload(run_id=run_id, request=request, route=Route.SPECIALIST_CLASSIFICATION_REVIEW,
            basis="Agent tool/step bound exceeded; confidence suppressed and specialist review required.",
            prompt_version=prompt_version, degraded=True, passages=list(retrieved.values()), trace=trace + tools.trace)
    supported = [item for item in candidates if item.get("kind") == "heading" and str(item.get("chapter", "")).zfill(2) in {"73", "96"}]
    if not supported:
        basis = "No relevant heading passage was found in the indexed official corpus; no HS code or policy is asserted."
        if not tools.all_chunks():
            basis = "Official tariff and export-policy PDFs are not indexed; safe specialist review is required and no HS code is asserted."
        trace.extend(tools.trace)
        return HandoffPayload(run_id=run_id, request=request, route=Route.SPECIALIST_CLASSIFICATION_REVIEW,
            basis=basis, prompt_version=prompt_version, passages=list(retrieved.values()), trace=trace)

    best = supported[0]
    heading_id = str(best.get("identifier", ""))
    heading_code = str(best.get("heading", ""))
    if not heading_code.isdigit():
        heading_code = "".join(ch for ch in heading_id if ch.isdigit())[-4:]
    gri = None
    for rule in GRI_ORDER:
        gri = tools.get_clause(rule)
        if gri:
            break
    policy = tools.policy_lookup(heading_code) if heading_code else None
    notes = tools.list_notes_for(str(best.get("chapter", "")))
    retrieved[best["chunk_id"]] = best
    if gri:
        retrieved[gri["chunk_id"]] = gri
    if policy:
        retrieved[policy["chunk_id"]] = policy
    citations = []
    for item in (best, gri, policy):
        if item:
            citations.append(Citation(chunk_id=str(item["chunk_id"]), identifier=str(item.get("identifier", "")),
                doc=str(item.get("doc", "")), page=item.get("page"), excerpt=str(item.get("text", ""))[:500]))
    # An indexed heading alone is never enough to claim the classification or export policy.
    if not gri or not policy or not heading_code:
        trace.extend(tools.trace)
        return HandoffPayload(run_id=run_id, request=request, route=Route.SPECIALIST_CLASSIFICATION_REVIEW,
            basis="A candidate heading was retrieved, but the required GRI rule or exact DGFT policy row was not independently supported.",
            citations=citations, passages=list(retrieved.values()) + notes, prompt_version=prompt_version, trace=trace)
    # Ambiguity after the initial GRI review is intentionally escalated rather than guessed.
    route = Route.SPECIALIST_CLASSIFICATION_REVIEW
    basis = "Evidence was retrieved; this implementation requires human confirmation of notes, GRI application, and policy conditions before clearance."
    trace.extend(tools.trace)
    return HandoffPayload(run_id=run_id, request=request, proposed_hs_code=None, rule_applied=None, route=route,
        basis=basis, citations=citations, passages=list(retrieved.values()) + notes,
        export_policy=None, prompt_version=prompt_version, trace=trace)
