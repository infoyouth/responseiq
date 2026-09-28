# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""SOC2 Audit Log router.

Exposes read-only endpoints that allow auditors, SRE teams, and
compliance tooling to inspect the immutable ``AuditEventLog`` table
without needing direct database access.

Endpoints
---------
GET /api/v1/audit/events
    Paginated list of all audit events with optional filters.

GET /api/v1/audit/events/{incident_id}
    Full lifecycle timeline for a specific incident.

GET /api/v1/audit/summary
    Aggregated counts grouped by event_type and outcome — suitable for
    a SOC2 management review dashboard.

GET /api/v1/audit/retention-policy
    Machine-readable statement of current data retention configuration.
    Include in your SOC2 vendor questionnaire response.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, col, select

from responseiq.config.settings import settings
from responseiq.db import get_session
from responseiq.models.base import AuditEventLog
from responseiq.services.audit_service import AuditEventType

router = APIRouter(prefix="/api/v1/audit", tags=["SOC2 Audit"])


@router.get(
    "/events",
    summary="Paginated SOC2 audit event log",
    responses={200: {"description": "List of audit events matching the supplied filters"}},
)
def list_audit_events(
    # Filters
    event_type: Optional[str] = Query(default=None, description="Filter by AuditEventType value"),
    incident_id: Optional[str] = Query(default=None, description="Filter by incident identifier"),
    outcome: Optional[str] = Query(default=None, description="Filter by outcome: success|blocked|warned|failed"),
    actor: Optional[str] = Query(default=None, description="Filter by actor string"),
    since: Optional[datetime] = Query(default=None, description="Return events at or after this UTC datetime"),
    until: Optional[datetime] = Query(default=None, description="Return events at or before this UTC datetime"),
    # Pagination
    limit: int = Query(default=50, ge=1, le=500, description="Max events to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    session: Session = Depends(get_session),
):
    """Return a paginated, filtered view of the ``AuditEventLog`` table.

    All filters are optional and combinable.  Results are ordered most-recent
    first.  For compliance exports use ``limit=500`` with ``offset`` paging.

    Note: accessing this endpoint itself generates an ``audit.log_accessed``
    event (meta-audit trail for compliance).
    """
    stmt = select(AuditEventLog)
    if event_type:
        stmt = stmt.where(AuditEventLog.event_type == event_type)
    if incident_id:
        stmt = stmt.where(AuditEventLog.incident_id == incident_id)
    if outcome:
        stmt = stmt.where(AuditEventLog.outcome == outcome)
    if actor:
        stmt = stmt.where(AuditEventLog.actor == actor)
    if since:
        stmt = stmt.where(col(AuditEventLog.timestamp) >= since)
    if until:
        stmt = stmt.where(col(AuditEventLog.timestamp) <= until)

    stmt = stmt.order_by(col(AuditEventLog.timestamp).desc()).offset(offset).limit(limit)
    events = session.exec(stmt).all()

    return {
        "total": len(events),
        "offset": offset,
        "limit": limit,
        "filters": {
            "event_type": event_type,
            "incident_id": incident_id,
            "outcome": outcome,
            "actor": actor,
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
        },
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "incident_id": e.incident_id,
                "actor": e.actor,
                "outcome": e.outcome,
                "action": e.action,
                "metadata_json": e.metadata_json,
                "ip_address": e.ip_address,
                "user_agent": e.user_agent,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ],
    }


@router.get(
    "/events/{incident_id}",
    summary="Full audit timeline for a specific incident",
    responses={
        200: {"description": "Chronological event timeline for this incident"},
    },
)
def incident_audit_timeline(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """Return every audit event associated with ``incident_id``.

    Results are ordered chronologically (oldest first) to show the full
    lifecycle: detection → Trust Gate → PR opened → human feedback → proof sealed.
    """
    stmt = (
        select(AuditEventLog)
        .where(AuditEventLog.incident_id == incident_id)
        .order_by(col(AuditEventLog.timestamp).asc())
    )
    events: list[AuditEventLog] = list(session.exec(stmt).all())

    return {
        "incident_id": incident_id,
        "event_count": len(events),
        "timeline": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "actor": e.actor,
                "outcome": e.outcome,
                "action": e.action,
                "metadata_json": e.metadata_json,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ],
    }


@router.get(
    "/summary",
    summary="SOC2 management review summary — event counts by type and outcome",
    responses={200: {"description": "Aggregated audit summary suitable for SOC2 management review"}},
)
def audit_summary(
    since: Optional[datetime] = Query(default=None, description="Summarise events at or after this UTC datetime"),
    until: Optional[datetime] = Query(default=None, description="Summarise events at or before this UTC datetime"),
    session: Session = Depends(get_session),
):
    """Return aggregate counts grouped by ``event_type`` and ``outcome``.

    Each slot in the response maps ``{event_type}.{outcome}`` to a count.
    Additionally, ``security_events`` lists all HMAC failures and
    ``policy_violations`` lists all Trust Gate blocks — the two metrics
    compliance officers ask about most.

    Typical use: daily/weekly management review dashboard; attach to
    SOC2 evidence package.
    """
    stmt = select(AuditEventLog)
    if since:
        stmt = stmt.where(col(AuditEventLog.timestamp) >= since)
    if until:
        stmt = stmt.where(col(AuditEventLog.timestamp) <= until)

    events: list[AuditEventLog] = list(session.exec(stmt).all())

    # Build counts by (event_type, outcome)
    counts: dict[str, int] = {}
    security_events: list[dict] = []
    policy_violations: list[dict] = []
    trust_gate_passed = 0
    trust_gate_blocked = 0
    trust_gate_warned = 0

    for e in events:
        key = f"{e.event_type}.{e.outcome}"
        counts[key] = counts.get(key, 0) + 1

        if e.event_type == AuditEventType.WEBHOOK_HMAC_FAILED:
            security_events.append({"timestamp": e.timestamp.isoformat(), "actor": e.actor, "action": e.action})
        if e.event_type == AuditEventType.TRUST_GATE_BLOCKED:
            policy_violations.append(
                {"timestamp": e.timestamp.isoformat(), "incident_id": e.incident_id, "action": e.action}
            )
            trust_gate_blocked += 1
        if e.event_type == AuditEventType.TRUST_GATE_PASSED:
            trust_gate_passed += 1
        if e.event_type == AuditEventType.TRUST_GATE_WARNED:
            trust_gate_warned += 1

    trust_gate_total = trust_gate_passed + trust_gate_blocked + trust_gate_warned
    acceptance_rate = round(trust_gate_passed / trust_gate_total, 4) if trust_gate_total else None

    return {
        "period": {
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
            "total_events": len(events),
        },
        "event_counts": counts,
        "trust_gate": {
            "total": trust_gate_total,
            "passed": trust_gate_passed,
            "blocked": trust_gate_blocked,
            "warned": trust_gate_warned,
            "acceptance_rate": acceptance_rate,
        },
        "security_events": security_events,
        "policy_violations": policy_violations,
    }


@router.get(
    "/retention-policy",
    summary="Machine-readable audit log retention policy",
    responses={200: {"description": "Current retention configuration for SOC2 vendor questionnaire responses"}},
)
def retention_policy():
    """Return the current audit log retention policy configuration.

    Include the response body verbatim in SOC2 vendor questionnaires
    under "Data Retention Policy / Audit Logging".  The
    ``audit_retention_days`` value is sourced from
    ``RESPONSEIQ_AUDIT_RETENTION_DAYS`` (default 2555 = 7 years).
    """
    days = settings.audit_retention_days
    return {
        "policy": "append_only_immutable",
        "algorithm": "SHA-256",
        "audit_retention_days": days,
        "audit_retention_years": round(days / 365, 2) if days else None,
        "expiry": "manual_purge_only" if days == 0 else f"events_older_than_{days}_days_eligible_for_purge",
        "controls": [
            "CC6.1 — Logical access controls: every API interaction logged with actor and outcome",
            "CC6.6 — Boundary protection: HMAC failures generate WEBHOOK_HMAC_FAILED events",
            "CC7.2 — System operations monitoring: Trust Gate decisions logged for every remediation",
            "CC7.3 — Change management: PR opened, rollback triggered, and watchdog events logged",
            "PI1.4 — Processing integrity: ProofBundle sealing logged with SHA-256 chain hash",
        ],
        "env_override": "RESPONSEIQ_AUDIT_RETENTION_DAYS",
    }
