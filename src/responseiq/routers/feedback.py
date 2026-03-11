# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Human feedback and semantic similarity router.

Handles ``POST /api/v1/feedback`` (engineer approves or rejects a
suggested fix), ``GET /api/v1/feedback/{log_id}`` (accept/reject
summary), and ``GET /api/v1/incidents/{id}/similar`` (cosine-similarity
ranked list of past incidents via text-embedding vectors).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from responseiq.db import get_session
from responseiq.models.base import FeedbackRecord
from responseiq.schemas.feedback import FeedbackIn, FeedbackOut, FeedbackSummary
from responseiq.schemas.semantic import SimilaritySearchResult
from responseiq.services.audit_service import AuditEventType, log_event_sync
from responseiq.services.semantic_search_service import SemanticSearchService
from responseiq.utils.logger import logger
from responseiq.utils.tracing import score_langfuse

router = APIRouter(prefix="/api/v1", tags=["feedback"])


# ── P-F1: Feedback ──────────────────────────────────────────────────────────


@router.post(
    "/feedback",
    response_model=FeedbackOut,
    status_code=201,
    summary="Record human approval/rejection of a remediation",
)
def submit_feedback(payload: FeedbackIn, session=Depends(get_session)):
    """
    Persist a human feedback signal and score the associated Langfuse trace.

    - ``approved=true``  → score 1.0 (accepted fix)
    - ``approved=false`` → score 0.0 (rejected fix)

    The Langfuse score is labelled ``human_approval`` and is linked to any
    Langfuse generation span whose metadata includes the matching ``log_id``.
    See ``responseiq.utils.tracing.score_langfuse`` for details.
    """
    record = FeedbackRecord(
        log_id=payload.log_id,
        approved=payload.approved,
        comment=payload.comment,
        created_at=datetime.now(timezone.utc),
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    # Score the Langfuse trace for this log (no-op when Langfuse not configured)
    score_langfuse(
        trace_name=f"log_{payload.log_id}",
        score_name="human_approval",
        value=1.0 if payload.approved else 0.0,
        comment=payload.comment,
    )

    logger.info(
        "Feedback recorded",
        log_id=payload.log_id,
        approved=payload.approved,
        record_id=record.id,
    )
    log_event_sync(
        AuditEventType.HUMAN_FEEDBACK_SUBMITTED,
        f"Human feedback submitted for log {payload.log_id}: {'approved' if payload.approved else 'rejected'}",
        incident_id=str(payload.log_id),
        actor="user",
        outcome="success",
        metadata={"approved": payload.approved, "comment": payload.comment},
    )
    return FeedbackOut(
        id=record.id,  # type: ignore[arg-type]
        log_id=record.log_id,
        approved=record.approved,
        comment=record.comment,
        created_at=record.created_at,
    )


@router.get(
    "/feedback/{log_id}",
    response_model=FeedbackSummary,
    summary="Feedback summary for a log",
)
def get_feedback(log_id: int, session=Depends(get_session)):
    """
    Return aggregated feedback statistics for a given ``log_id``.

    ``acceptance_rate`` is the primary KPI: it measures how often engineers
    approve the AI-generated remediations for this class of incident.
    """
    from sqlmodel import select

    records = session.exec(select(FeedbackRecord).where(FeedbackRecord.log_id == log_id)).all()

    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"No feedback found for log_id={log_id}",
        )

    approvals = sum(1 for r in records if r.approved)
    rejections = len(records) - approvals
    last = max(records, key=lambda r: r.created_at)

    return FeedbackSummary(
        log_id=log_id,
        total=len(records),
        approvals=approvals,
        rejections=rejections,
        acceptance_rate=round(approvals / len(records), 4),
        last_feedback_at=last.created_at,
    )


# ── P-F2: Semantic Similarity ────────────────────────────────────────────────


@router.get(
    "/incidents/{incident_id}/similar",
    response_model=SimilaritySearchResult,
    summary="Find semantically similar past incidents",
)
def find_similar_incidents(
    incident_id: int,
    threshold: float = Query(default=0.92, ge=0.0, le=1.0, description="Cosine similarity threshold"),
    limit: int = Query(default=10, ge=1, le=50),
    session=Depends(get_session),
):
    """
    Return incidents with cosine similarity ≥ ``threshold`` to incident
    ``incident_id``.

    Requires that embeddings have already been generated for the incidents
    involved (triggered automatically via the ARQ ``generate_embedding_job``
    after each incident is created — or manually via the worker).

    Results are sorted by similarity descending and capped at ``limit``.
    A ``similarity_score ≥ 0.92`` indicates a near-duplicate — the same
    root cause with likely the same fix.
    """
    svc = SemanticSearchService(session)
    result = svc.find_similar(incident_id, threshold=threshold, limit=limit)

    if result.results:
        logger.info(
            "Semantic similarity: found %d similar incidents for incident_id=%d",
            len(result.results),
            incident_id,
        )

    return result
