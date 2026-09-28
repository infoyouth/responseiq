# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Temporal activities for the ResponseIQ remediation workflow.

Each activity wraps an existing service call as a retriable, idempotent async
function. Temporal replays these on failure so they must not have side effects
that cannot be safely re-run. Registered: ``analyze_incident_activity``,
``generate_embedding_activity``, ``score_remediation_activity``, and
``notify_human_review_activity``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from responseiq.utils.logger import logger

# Guard: apply @activity.defn only when temporalio is installed
try:
    from temporalio import activity as _ta  # type: ignore[import-untyped]

    _activity_defn = _ta.defn
    _HAS_TEMPORAL = True
except ImportError:
    _HAS_TEMPORAL = False

    def _activity_defn(func):  # type: ignore[misc]
        """No-op decorator when temporalio is not installed."""
        return func


# ── Input / Output dataclasses ────────────────────────────────────────────────


@dataclass
class AnalyzeActivityResult:
    log_id: int
    incident_created: bool
    description: Optional[str] = None
    severity: Optional[str] = None


# ── Activity definitions ───────────────────────────────────────────────────────


@_activity_defn
async def analyze_incident_activity(log_id: int) -> AnalyzeActivityResult:
    """
    Temporal activity: analyse a log row and create an Incident.

    Wraps the synchronous ``process_log_ingestion`` service in a thread to
    avoid blocking the event loop (Temporal best-practice for sync I/O).
    """
    import asyncio

    from responseiq.services.incident_service import process_log_ingestion

    logger.info("Temporal activity: analyze_incident", log_id=log_id)
    await asyncio.get_event_loop().run_in_executor(None, process_log_ingestion, log_id)

    # Fetch the created incident to return context
    try:
        from sqlmodel import Session, select

        from responseiq.db import get_engine
        from responseiq.models.base import Incident

        engine = get_engine()
        with Session(engine) as session:
            incident = session.exec(select(Incident).where(Incident.log_id == log_id)).first()
            if incident:
                return AnalyzeActivityResult(
                    log_id=log_id,
                    incident_created=True,
                    description=incident.description,
                    severity=incident.severity,
                )
    except Exception as exc:
        logger.warning("Temporal activity: incident fetch failed: %s", exc)

    return AnalyzeActivityResult(log_id=log_id, incident_created=True)


@_activity_defn
async def generate_embedding_activity(log_id: int) -> None:
    """
    Temporal activity: generate and store semantic embedding for semantic
    dedup (P-F2). No-op when OpenAI is unavailable.
    """
    try:
        from sqlmodel import Session, select

        from responseiq.db import get_engine
        from responseiq.models.base import Incident
        from responseiq.services.semantic_search_service import SemanticSearchService

        engine = get_engine()
        with Session(engine) as session:
            incident = session.exec(select(Incident).where(Incident.log_id == log_id)).first()
            if incident and incident.id:
                svc = SemanticSearchService(session)
                await svc.generate_and_store.__wrapped__(svc, incident.id)  # type: ignore[attr-defined]
    except AttributeError:
        # generate_and_store is not async — run it in executor
        import asyncio

        from sqlmodel import Session, select

        from responseiq.db import get_engine
        from responseiq.models.base import Incident
        from responseiq.services.semantic_search_service import SemanticSearchService

        def _sync_embed():
            engine = get_engine()
            with Session(engine) as session:
                incident = session.exec(select(Incident).where(Incident.log_id == log_id)).first()
                if incident and incident.id:
                    svc = SemanticSearchService(session)
                    import asyncio as _asyncio

                    _asyncio.get_event_loop().run_until_complete(svc.generate_and_store(incident.id))

        await asyncio.get_event_loop().run_in_executor(None, _sync_embed)
    except Exception as exc:
        logger.warning("Temporal activity: generate_embedding failed (non-fatal): %s", exc)


@_activity_defn
async def score_remediation_activity(
    log_id: int,
    approved: bool,
    comment: str = "",
) -> None:
    """
    Temporal activity: score the Langfuse LLM trace for this log (P-F1).
    No-op when Langfuse is not configured.
    """
    from responseiq.utils.tracing import score_langfuse

    score_langfuse(
        trace_name=f"log_{log_id}",
        score_name="human_approval",
        value=1.0 if approved else 0.0,
        comment=comment or None,
    )
    logger.info(
        "Temporal activity: scored remediation",
        log_id=log_id,
        approved=approved,
    )


@_activity_defn
async def notify_human_review_activity(log_id: int, summary: str) -> None:
    """
    Temporal activity: notify an engineer that human review is required.

    Currently logs the notification.  Wire to Slack/PagerDuty/email by
    calling ``notification_service`` here.
    """
    logger.info(
        "Temporal activity: human review requested",
        log_id=log_id,
        summary=summary[:200],
    )
    # TODO(P-F4 v2): call notification_service.send_approval_request(log_id, summary)


# ── Registry for WorkerSettings.activities ────────────────────────────────────

ALL_ACTIVITIES = [
    analyze_incident_activity,
    generate_embedding_activity,
    score_remediation_activity,
    notify_human_review_activity,
]
