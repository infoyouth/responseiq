# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""FastAPI application entry point.

Mounts all routers and exposes webhook ingestion endpoints for Datadog,
PagerDuty, and Sentry. Run with::

    uv run uvicorn responseiq.app:app --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import select

from .db import get_session, init_db
from .models.base import Incident, Log
from .routers.blueprints import router as blueprints_router
from .routers.causal_graph import router as causal_graph_router
from .routers.conversations import router as conversations_router
from .routers.feedback import router as feedback_router
from .routers.github_pr import router as github_pr_router
from .routers.proof_record import router as proof_record_router
from .routers.shadow_report import router as shadow_report_router
from .routers.streaming import router as streaming_router
from .routers.watchdog import router as watchdog_router
from .routers.webhooks import router as webhooks_router
from .schemas.incident import IncidentOut
from .schemas.log import LogIn, LogOut
from .services.impact import assess_impact
from .services.incident_service import process_log_ingestion

# Initialize logging/telemetry early
from .utils.logger import logger
from .utils.telemetry import setup_telemetry
from .utils.tracing import flush_langfuse
from .worker import create_arq_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    setup_telemetry(app)
    # ARQ Redis pool — None when ARQ_REDIS_URL is not configured (BackgroundTasks fallback)
    app.state.arq_pool = await create_arq_pool()
    # Temporal worker (P-F4) — only starts when TEMPORAL_ENABLED=true and temporalio installed
    from .config.settings import settings as _settings

    if _settings.temporal_enabled:
        from .temporal.worker import start_temporal_worker

        app.state.temporal_worker = await start_temporal_worker()
    else:
        app.state.temporal_worker = None
    logger.info("Service started successfully.")
    yield
    if app.state.arq_pool is not None:
        await app.state.arq_pool.aclose()
    if getattr(app.state, "temporal_worker", None) is not None:
        app.state.temporal_worker.cancel()
    flush_langfuse()
    logger.info("Service stopping.")


app = FastAPI(
    title="ResponseIQ",
    lifespan=lifespan,
)


def _build_incident_outputs(items: List[Incident]) -> List[IncidentOut]:
    recurrences: dict[tuple[str, str], int] = {}
    for incident in items:
        title = incident.description or incident.severity or "incident"
        key = ((incident.severity or "medium").lower(), title)
        recurrences[key] = recurrences.get(key, 0) + 1

    incidents: List[IncidentOut] = []
    for incident in items:
        title = incident.description or incident.severity or "incident"
        key = ((incident.severity or "medium").lower(), title)
        impact = assess_impact(
            severity=incident.severity,
            title=title,
            description=incident.description,
            source=incident.source,
            recurrence=recurrences.get(key, 1),
        )
        incidents.append(
            IncidentOut(
                id=incident.id,
                title=title,
                severity=incident.severity,
                description=incident.description or "",
                source=incident.source or "unknown",
                impact_score=impact.score,
                impact_factors=impact.factors,
            )
        )

    incidents.sort(key=lambda current: current.impact_score or 0.0, reverse=True)
    return incidents


# Global Exception Handler for reliability
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unexpected system error.")
    return JSONResponse(
        status_code=500,
        content={"detail": "System encountered an error", "trace_id": "refer_to_logs"},
    )


# include routers

app.include_router(blueprints_router)
app.include_router(webhooks_router)
app.include_router(feedback_router)
app.include_router(conversations_router)
app.include_router(github_pr_router)
app.include_router(causal_graph_router)  # P6: Causal Root-Cause Graph
app.include_router(shadow_report_router)  # v2.17.0: PDF/CSV Pilot Report
app.include_router(proof_record_router)  # v2.18.0 #2: ProofBundle audit endpoint
app.include_router(watchdog_router)  # v2.18.0 #3: Post-apply watchdog
app.include_router(streaming_router)  # P-Modern-3: SSE streaming analysis endpoint

# serve static UI
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/ui/blueprints")
def blueprints_ui():
    return RedirectResponse(url="/static/blueprints.html")


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


POST_LOG_EXAMPLE = {
    "message": "critical: panic when allocating resource",
    "severity": "high",
}


@app.post(
    "/logs",
    status_code=202,
    response_model=LogOut,
    summary="Ingest log entry",
)
def ingest_log(
    payload: LogIn,
    background_tasks: BackgroundTasks,
    session=Depends(get_session),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
):
    # optional API key enforcement for ingestion
    required_key = __import__("os").environ.get("LOG_INGEST_API_KEY")
    if required_key and x_api_key != required_key:
        raise HTTPException(status_code=401, detail="invalid api key")

    # 1. Persist Log
    log = Log(message=payload.message, severity=payload.severity)
    session.add(log)
    session.commit()
    session.refresh(log)

    if not log.id:
        raise HTTPException(status_code=500, detail="Database failure: Log ID not generated")

    # 2. Assign analysis task
    background_tasks.add_task(process_log_ingestion, log.id)

    return LogOut(
        id=log.id,
        message=log.message,
        severity=log.severity,
    )


@app.get(
    "/incidents",
    response_model=List[IncidentOut],
    summary="List incidents",
)
def list_incidents(
    severity: str | None = None,
    session=Depends(get_session),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
):
    # optional API key enforcement for reading incidents
    read_key = __import__("os").environ.get("LOG_READ_API_KEY")
    if read_key and x_api_key != read_key:
        raise HTTPException(status_code=401, detail="invalid api key")
    q = select(Incident)
    if severity:
        q = q.where(Incident.severity == severity)
    results = session.exec(q).all()
    return _build_incident_outputs(results)


# ...existing code above handles app and endpoints
