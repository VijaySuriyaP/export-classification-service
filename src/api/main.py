"""FastAPI gateway with async queueing, quarantine, trace and feedback."""
from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from uuid import uuid4
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import func, select, text

from src.api.queue import enqueue
from src.api.ratelimit import allow_request
from src.api.validation import validate_request
from src.common.db import FeedbackRecord, QuarantineRecord, RunRecord, RunStep, SessionLocal, init_db
from src.common.logging import configure_logging, correlation_id_var

configure_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize persistent tables before accepting requests."""
    init_db()
    yield

app = FastAPI(title="Export Classification Check Service", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
REQUESTS = Counter("export_api_requests_total", "API requests", ["method", "path", "status"])
LATENCY = Histogram("export_api_request_latency_seconds", "API request latency")


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    """Propagate or create a correlation ID and record basic request metrics."""
    correlation_id = request.headers.get("x-correlation-id") or str(uuid4())
    token = correlation_id_var.set(correlation_id)
    started = time.monotonic()
    try:
        response = await call_next(request)
        response.headers["x-correlation-id"] = correlation_id
        route = request.scope.get("route")
        metric_path = getattr(route, "path", request.url.path)
        REQUESTS.labels(request.method, metric_path, str(response.status_code)).inc()
        return response
    finally:
        LATENCY.observe(time.monotonic() - started)
        correlation_id_var.reset(token)



@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe; does not depend on external services."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> JSONResponse:
    """Readiness probe checks durable DB connectivity."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return JSONResponse({"status": "ready"})
    except Exception:
        return JSONResponse({"status": "not_ready"}, status_code=503)


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    """Prometheus-compatible request and latency metrics."""
    return PlainTextResponse(generate_latest().decode(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/classify", status_code=202)
async def classify(request: Request) -> JSONResponse:
    """Validate and enqueue a request, returning a run ID for async polling."""
    try:
        raw = await request.json()
    except Exception:
        raw = {"_raw_body_unparseable": True}
    model, errors = validate_request(raw)
    if model is None:
        with SessionLocal() as session:
            session.add(QuarantineRecord(raw_request=raw if isinstance(raw, dict) else {"value": str(raw)},
                errors=errors, correlation_id=correlation_id_var.get()))
            session.commit()
        return JSONResponse({"status": "rejected", "errors": errors, "quarantined": True}, status_code=422)
    allowed, retry_after = allow_request(model.client_id)
    if not allowed:
        return JSONResponse({"detail": "rate limit exceeded", "retry_after": retry_after}, status_code=429,
            headers={"Retry-After": str(retry_after)})
    run_id = str(uuid4())
    with SessionLocal() as session:
        session.add(RunRecord(id=run_id, client_request_id=str(model.client_request_id), client_id=model.client_id,
            request_data=model.model_dump(mode="json"), status="queued"))
        session.commit()
    try:
        enqueue(run_id)
    except Exception as exc:
        with SessionLocal() as session:
            record = session.get(RunRecord, run_id)
            if record:
                record.status = "failed_escalated"
                record.error = "queue_unavailable"
                record.result = {"run_id": run_id, "status": "failed_escalated", "route": "specialist-classification-review",
                    "basis": "Queue unavailable; no classification asserted.", "proposed_hs_code": None, "citations": [], "degraded": True}
                session.commit()
        logger.error("queue enqueue failed: %s", type(exc).__name__)
        return JSONResponse({"detail": "queue unavailable", "run_id": run_id}, status_code=503)
    return JSONResponse({"run_id": run_id, "status": "queued"}, status_code=202)


@app.get("/v1/runs/{run_id}")
def get_run(run_id: str) -> JSONResponse:
    """Fetch the current state and terminal result of a submitted run."""
    with SessionLocal() as session:
        record = session.get(RunRecord, run_id)
        if not record:
            return JSONResponse({"detail": "run not found"}, status_code=404)
        payload: dict[str, Any] = {"run_id": record.id, "status": record.status, "created_at": record.created_at}
        if record.result:
            payload.update(record.result)
        if record.error:
            payload["error"] = record.error
        return JSONResponse(json.loads(json.dumps(payload, default=str)))


@app.get("/v1/runs/{run_id}/trace")
def get_trace(run_id: str) -> JSONResponse:
    """Reconstruct input, final result and ordered step events for a run."""
    with SessionLocal() as session:
        record = session.get(RunRecord, run_id)
        if not record:
            return JSONResponse({"detail": "run not found"}, status_code=404)
        steps = session.scalars(select(RunStep).where(RunStep.run_id == run_id).order_by(RunStep.id)).all()
        return JSONResponse({"run_id": run_id, "request": record.request_data, "status": record.status,
            "result": record.result, "steps": [{"step": s.step_name, "detail": s.detail,
            "latency_ms": s.latency_ms, "prompt_version": s.prompt_version} for s in steps]})


@app.post("/v1/runs/{run_id}/feedback", status_code=201)
async def feedback(run_id: str, request: Request) -> JSONResponse:
    """Record human feedback on an existing completed or escalated run."""
    try:
        raw = await request.json()
        satisfactory = raw["satisfactory"]
        reason = str(raw.get("reason", ""))[:2000]
        if not isinstance(satisfactory, bool):
            raise ValueError("satisfactory must be boolean")
    except Exception:
        return JSONResponse({"detail": "body requires boolean satisfactory and optional reason"}, status_code=422)
    with SessionLocal() as session:
        if not session.get(RunRecord, run_id):
            return JSONResponse({"detail": "run not found"}, status_code=404)
        session.add(FeedbackRecord(run_id=run_id, satisfactory=satisfactory, reason=reason))
        session.commit()
    return JSONResponse({"status": "recorded", "run_id": run_id}, status_code=201)


@app.get("/v1/feedback/summary")
def feedback_summary() -> dict[str, Any]:
    """Summarize stored human feedback counts."""
    with SessionLocal() as session:
        rows = session.execute(select(FeedbackRecord.satisfactory, func.count()).group_by(FeedbackRecord.satisfactory)).all()
    counts = {"satisfactory": 0, "unsatisfactory": 0}
    for satisfactory, count in rows:
        counts["satisfactory" if satisfactory else "unsatisfactory"] = count
    return {"count": sum(counts.values()), "counts": counts}
