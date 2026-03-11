# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Real-time webhook ingestion router.

Exposes ingest endpoints for Datadog, PagerDuty, and Sentry, plus a
Server-Sent Events stream (``GET /incidents/{log_id}/stream``) that
pushes remediation progress to clients in real time. This is the
first step in the pipeline: Detect → Context → Reason → Execute.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import time
from typing import AsyncGenerator, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlmodel import Session, select

from ..config.settings import settings
from ..db import get_engine, get_session
from ..services.audit_service import AuditEventType, log_event_sync
from ..models.base import Incident, Log
from ..schemas.webhooks import (
    DatadogWebhookPayload,
    PagerDutyWebhookPayload,
    SSEEvent,
    SentryWebhookPayload,
    WebhookAck,
    WebhookIncident,
)
from ..services.incident_service import process_log_ingestion
from ..utils.logger import logger


async def _enqueue_or_bg(
    log_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
) -> None:
    """
    Enqueue ``process_log_ingestion`` as a durable ARQ job when a Redis pool
    is available on ``app.state.arq_pool``, otherwise fall back to
    FastAPI BackgroundTasks (fire-and-forget, no retry).
    """
    arq_pool = getattr(getattr(request, "app", None), "state", None)
    arq_pool = getattr(arq_pool, "arq_pool", None) if arq_pool else None
    if arq_pool is not None:
        await arq_pool.enqueue_job("process_log_ingestion_job", log_id)
        logger.info("ARQ job enqueued", log_id=log_id)
    else:
        background_tasks.add_task(process_log_ingestion, log_id)
        logger.debug("BackgroundTasks fallback used (no ARQ pool)", log_id=log_id)


router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# ---------------------------------------------------------------------------
# Idempotency store  (replace with Redis in multi-process deployments)
# ---------------------------------------------------------------------------

_SEEN_KEYS: Dict[str, float] = {}  # { fingerprint → timestamp_inserted }
_IDEMPOTENCY_TTL = 3600.0  # 1 hour


def _evict_expired() -> None:
    """Remove entries older than TTL.  Called on every ingest to avoid unbounded growth."""
    cutoff = time.monotonic() - _IDEMPOTENCY_TTL
    expired = [k for k, ts in _SEEN_KEYS.items() if ts < cutoff]
    for k in expired:
        del _SEEN_KEYS[k]


def _is_duplicate(key: str) -> bool:
    _evict_expired()
    if key in _SEEN_KEYS:
        return True
    _SEEN_KEYS[key] = time.monotonic()
    return False


# ---------------------------------------------------------------------------
# HMAC signature verification
# ---------------------------------------------------------------------------

_DATADOG_SIG_HEADER = "x-datadog-webhook-signature"  # sha256=HEX
_PAGERDUTY_SIG_HEADER = "x-pagerduty-signature"  # v1=HEX,...
_SENTRY_SIG_HEADER = "sentry-hook-signature"  # HEX (no prefix)


def _verify_hmac(
    secret: Optional[str],
    body: bytes,
    received: Optional[str],
    *,
    prefix: str = "",
) -> None:
    """
    Verify HMAC-SHA256 signature when ``secret`` is configured.

    Raises HTTP 403 when:
    - Secret is configured and ``received`` header is missing.
    - Signature does not match.

    Does nothing (allows request through) when secret is not configured.

    Parameters
    ----------
    prefix:
        Optional prefix to strip before hex comparison
        (e.g. ``"sha256="`` for Datadog, ``"v1="`` for PagerDuty).
    """
    if not secret:
        return  # Signature verification not configured — skip

    if not received:
        raise HTTPException(status_code=403, detail="Missing webhook signature header")

    # Strip prefix / take first signature when multiple are present (PagerDuty allows comma-list)
    candidate = received.split(",")[0].strip()
    if prefix and candidate.startswith(prefix):
        candidate = candidate[len(prefix) :]

    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, candidate):
        logger.warning("Webhook signature mismatch — request rejected")
        log_event_sync(
            AuditEventType.WEBHOOK_HMAC_FAILED,
            "Webhook HMAC-SHA256 signature mismatch — request rejected (403)",
            actor="webhook:unknown",
            outcome="failed",
            metadata={"detail": "Invalid webhook signature"},
        )
        raise HTTPException(status_code=403, detail="Invalid webhook signature")


# ---------------------------------------------------------------------------
# Payload normalisers
# ---------------------------------------------------------------------------


def _severity_from_datadog(alert_type: Optional[str], priority: Optional[str]) -> str:
    """Map Datadog alert_type / priority to internal severity."""
    if priority:
        mapping = {"P1": "critical", "P2": "high", "P3": "medium", "P4": "low", "P5": "low"}
        return mapping.get(priority.upper(), "medium")
    mapping = {"error": "high", "warning": "medium", "info": "low", "success": "low"}
    return mapping.get((alert_type or "").lower(), "medium")


def _severity_from_pagerduty(urgency: Optional[str]) -> str:
    return "high" if urgency == "high" else "medium"


def _severity_from_sentry(level: Optional[str]) -> str:
    mapping = {"fatal": "critical", "error": "high", "warning": "medium", "info": "low", "debug": "low"}
    return mapping.get((level or "").lower(), "medium")


def _make_idempotency_key(source: str, title: str, log_content: str) -> str:
    fingerprint = f"{source}:{title}:{log_content[:256]}"
    return hashlib.sha256(fingerprint.encode()).hexdigest()


def _normalize_datadog(payload: DatadogWebhookPayload) -> WebhookIncident:
    title = payload.msg_title or payload.title or "Datadog alert"
    log_content = payload.msg_text or payload.body or title
    severity = _severity_from_datadog(payload.alert_type, payload.priority or payload.severity)
    return WebhookIncident(
        source="datadog",
        title=title,
        severity=severity,
        log_content=log_content,
        idempotency_key=_make_idempotency_key("datadog", title, log_content),
        raw_payload=payload.model_dump(),
    )


def _normalize_pagerduty(payload: PagerDutyWebhookPayload) -> WebhookIncident:
    data = payload.event.data
    title = data.title or payload.event.event_type or "PagerDuty incident"
    details = (data.body or {}).get("details", "")
    log_content = details or title
    severity = _severity_from_pagerduty(data.urgency)
    return WebhookIncident(
        source="pagerduty",
        title=title,
        severity=severity,
        log_content=log_content,
        idempotency_key=_make_idempotency_key("pagerduty", title, log_content),
        raw_payload=payload.model_dump(),
    )


def _normalize_sentry(payload: SentryWebhookPayload) -> WebhookIncident:
    issue_data = payload.data.get("issue", {})
    title = issue_data.get("title", "Sentry issue")
    level = issue_data.get("level", "error")
    culprit = issue_data.get("culprit", "")
    log_content = f"{title}\nCulprit: {culprit}" if culprit else title
    severity = _severity_from_sentry(level)
    return WebhookIncident(
        source="sentry",
        title=title,
        severity=severity,
        log_content=log_content,
        idempotency_key=_make_idempotency_key("sentry", title, log_content),
        raw_payload=payload.model_dump(),
    )


# ---------------------------------------------------------------------------
# Shared ingest helper
# ---------------------------------------------------------------------------


async def _ingest_webhook_incident(
    incident: WebhookIncident,
    background_tasks: BackgroundTasks,
    session: Session,
    request: Request,
) -> WebhookAck:
    """
    Persist the normalised incident as a ``Log`` row and enqueue background
    analysis.  Returns a ``WebhookAck`` with the created log_id.
    """
    # Deduplication check
    duplicate = _is_duplicate(incident.idempotency_key)
    if duplicate:
        logger.info(
            "Webhook duplicate detected — skipping re-ingestion",
            source=incident.source,
            idempotency_key=incident.idempotency_key[:16],
        )
        return WebhookAck(
            accepted=True,
            log_id=None,
            message="Duplicate event — already being processed.",
            idempotency_key=incident.idempotency_key,
            duplicate=True,
        )

    log = Log(
        message=f"[{incident.source.upper()}] {incident.title}\n\n{incident.log_content}",
        severity=incident.severity,
    )
    session.add(log)
    session.commit()
    session.refresh(log)

    if not log.id:
        raise HTTPException(status_code=500, detail="Database failure: Log ID not generated")

    await _enqueue_or_bg(log.id, background_tasks, request)

    logger.info(
        "Webhook incident ingested",
        source=incident.source,
        log_id=log.id,
        severity=incident.severity,
        title=incident.title[:80],
    )

    return WebhookAck(
        accepted=True,
        log_id=log.id,
        message=f"Incident ingested from {incident.source}. Poll GET /incidents/{log.id}/stream for progress.",
        idempotency_key=incident.idempotency_key,
        duplicate=False,
    )


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/datadog",
    response_model=WebhookAck,
    status_code=202,
    summary="Ingest Datadog monitor webhook",
)
async def ingest_datadog(
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    x_datadog_webhook_signature: Optional[str] = Header(default=None),
) -> WebhookAck:
    body = await request.body()
    secret = settings.datadog_webhook_secret
    secret_val = secret.get_secret_value() if secret else None
    _verify_hmac(secret_val, body, x_datadog_webhook_signature, prefix="sha256=")

    try:
        payload = DatadogWebhookPayload.model_validate_json(body)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422, detail=f"Invalid payload: {exc.error_count()} validation error(s)"
        ) from exc
    incident = _normalize_datadog(payload)
    return await _ingest_webhook_incident(incident, background_tasks, session, request)


@router.post(
    "/pagerduty",
    response_model=WebhookAck,
    status_code=202,
    summary="Ingest PagerDuty v3 event webhook",
)
async def ingest_pagerduty(
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    x_pagerduty_signature: Optional[str] = Header(default=None),
) -> WebhookAck:
    body = await request.body()
    secret = settings.pagerduty_webhook_secret
    secret_val = secret.get_secret_value() if secret else None
    _verify_hmac(secret_val, body, x_pagerduty_signature, prefix="v1=")

    try:
        payload = PagerDutyWebhookPayload.model_validate_json(body)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422, detail=f"Invalid payload: {exc.error_count()} validation error(s)"
        ) from exc
    incident = _normalize_pagerduty(payload)
    return await _ingest_webhook_incident(incident, background_tasks, session, request)


@router.post(
    "/sentry",
    response_model=WebhookAck,
    status_code=202,
    summary="Ingest Sentry issue/alert webhook",
)
async def ingest_sentry(
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    sentry_hook_signature: Optional[str] = Header(default=None),
) -> WebhookAck:
    body = await request.body()
    secret = settings.sentry_webhook_secret
    secret_val = secret.get_secret_value() if secret else None
    _verify_hmac(secret_val, body, sentry_hook_signature, prefix="")

    try:
        payload = SentryWebhookPayload.model_validate_json(body)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422, detail=f"Invalid payload: {exc.error_count()} validation error(s)"
        ) from exc
    incident = _normalize_sentry(payload)
    return await _ingest_webhook_incident(incident, background_tasks, session, request)


# ---------------------------------------------------------------------------
# SSE streaming endpoint
# ---------------------------------------------------------------------------

_SSE_POLL_INTERVAL = 1.0  # seconds between DB polls
_SSE_TIMEOUT = 120.0  # max seconds before sending timeout event


async def _sse_generator(log_id: int) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE-formatted strings.

    Polls the ``Incident`` table for a row with ``log_id=log_id`` until
    found or ``_SSE_TIMEOUT`` elapses.

    SSE format reference:
        data: {"status": "processing", "log_id": 42}\n\n
    """
    engine = get_engine()
    deadline = time.monotonic() + _SSE_TIMEOUT
    seen_incident_id: Optional[int] = None

    while time.monotonic() < deadline:
        with Session(engine) as session:
            incident: Optional[Incident] = session.exec(select(Incident).where(Incident.log_id == log_id)).first()

        if incident and incident.id != seen_incident_id:
            seen_incident_id = incident.id
            event = SSEEvent(
                log_id=log_id,
                status="complete",
                incident_id=incident.id,
                severity=incident.severity,
                description=incident.description,
                source=incident.source,
            )
            yield f"data: {event.model_dump_json()}\n\n"
            return  # Close stream — work is done

        # Still processing — send heartbeat every poll cycle
        heartbeat = SSEEvent(log_id=log_id, status="processing")
        yield f"data: {heartbeat.model_dump_json()}\n\n"
        await asyncio.sleep(_SSE_POLL_INTERVAL)

    # Timed out
    timeout_event = SSEEvent(log_id=log_id, status="timeout")
    yield f"data: {timeout_event.model_dump_json()}\n\n"


@router.get(
    "/stream/{log_id}",
    summary="Stream incident processing status (Server-Sent Events)",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": (
                "SSE stream.  Events have JSON ``data`` fields with keys: "
                "``log_id``, ``status`` (processing | complete | timeout), "
                "and — when complete — ``incident_id``, ``severity``, "
                "``description``, ``source``."
            ),
        }
    },
)
async def stream_incident_status(log_id: int) -> StreamingResponse:
    """
    Server-Sent Events endpoint.  Connect immediately after a webhook POST
    using the ``log_id`` from the ``WebhookAck`` response.

    Example::

        curl -N http://localhost:8000/webhooks/stream/42
    """
    return StreamingResponse(
        _sse_generator(log_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
