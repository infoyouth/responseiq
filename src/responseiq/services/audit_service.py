# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""SOC2 Audit Service — unified, immutable event log.

Every significant action in the ResponseIQ pipeline must call
``log_event()`` so auditors have a complete, tamper-evident timeline
that satisfies SOC2 Type II CC6.1 (Logical Access) and CC7.2
(System Operations Monitoring).

Design principles
-----------------
* **Append-only** — ``log_event()`` only inserts; no update path exists.
* **Fire-and-forget** — DB errors are swallowed and warned so audit
  failures never block the business-logic response path.
* **Zero-import-cycle** — this module imports only from ``models`` and
  ``db``; never from ``services.trust_gate`` or routers.

Usage::

    from responseiq.services.audit_service import AuditEventType, log_event

    await log_event(
        event_type=AuditEventType.TRUST_GATE_BLOCKED,
        incident_id=request.incident_id,
        actor="system",
        action=f"Trust Gate blocked incident {request.incident_id}: {result.reason}",
        outcome="blocked",
        metadata={"reason": result.reason, "checks_failed": result.checks_failed},
    )
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, Optional

from responseiq.db import get_session
from responseiq.models.base import AuditEventLog
from responseiq.utils.logger import logger


class AuditEventType(str, Enum):
    """Canonical event types for the SOC2 audit log.

    Grouped by subsystem so the audit summary endpoint can aggregate counts
    per-category without string parsing.
    """

    # ── Trust Gate ─────────────────────────────────────────────────────────
    TRUST_GATE_PASSED = "trust_gate.passed"
    TRUST_GATE_BLOCKED = "trust_gate.blocked"
    TRUST_GATE_WARNED = "trust_gate.warned"

    # ── Webhook / API Security ──────────────────────────────────────────────
    WEBHOOK_RECEIVED = "webhook.received"
    WEBHOOK_HMAC_FAILED = "webhook.hmac_failed"

    # ── Remediation Lifecycle ──────────────────────────────────────────────
    INCIDENT_ANALYZED = "incident.analyzed"
    PR_OPENED = "pr.opened"
    PR_COMMAND_DISPATCHED = "pr.command_dispatched"
    ROLLBACK_TRIGGERED = "rollback.triggered"
    WATCHDOG_TRIGGERED = "watchdog.triggered"
    WATCHDOG_COMPLETED = "watchdog.completed"

    # ── Human Actions ──────────────────────────────────────────────────────
    HUMAN_FEEDBACK_SUBMITTED = "feedback.submitted"

    # ── Proof / Integrity ──────────────────────────────────────────────────
    PROOF_BUNDLE_SEALED = "proof.sealed"

    # ── Audit Log Access (meta) ────────────────────────────────────────────
    AUDIT_LOG_ACCESSED = "audit.log_accessed"


def _write_audit_record(
    event_type: AuditEventType,
    action: str,
    *,
    incident_id: Optional[str] = None,
    actor: str = "system",
    outcome: str = "success",
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[AuditEventLog]:
    """Internal: write one ``AuditEventLog`` row and return it (or ``None`` on error)."""
    record = AuditEventLog(
        event_type=event_type.value,
        incident_id=incident_id,
        actor=actor,
        outcome=outcome,
        action=action[:500],
        metadata_json=json.dumps(metadata, default=str) if metadata else None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    try:
        with next(get_session()) as session:  # type: ignore[call-arg]
            session.add(record)
            session.commit()
            session.refresh(record)
        logger.debug(
            "📋 audit event logged",
            event_type=event_type.value,
            incident_id=incident_id,
            outcome=outcome,
        )
        return record
    except Exception as exc:
        logger.warning(
            "⚠️  audit_service: DB write failed — event NOT persisted",
            event_type=event_type.value,
            incident_id=incident_id,
            error=str(exc),
        )
        return None


async def log_event(
    event_type: AuditEventType,
    action: str,
    *,
    incident_id: Optional[str] = None,
    actor: str = "system",
    outcome: str = "success",
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[AuditEventLog]:
    """Append one immutable audit event to the ``AuditEventLog`` table.

    Async variant — use in ``async def`` route handlers and services.
    For sync route handlers use :func:`log_event_sync`.

    This function is intentionally **fire-and-forget**: if the DB write
    fails the exception is caught, logged as a warning, and ``None`` is
    returned.  Callers must never use the result for business-logic
    purposes — only for testing assertions.
    """
    return _write_audit_record(
        event_type=event_type,
        action=action,
        incident_id=incident_id,
        actor=actor,
        outcome=outcome,
        metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def log_event_sync(
    event_type: AuditEventType,
    action: str,
    *,
    incident_id: Optional[str] = None,
    actor: str = "system",
    outcome: str = "success",
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[AuditEventLog]:
    """Sync variant of :func:`log_event` for use in synchronous route handlers.

    Identical behaviour and fire-and-forget semantics.
    """
    return _write_audit_record(
        event_type=event_type,
        action=action,
        incident_id=incident_id,
        actor=actor,
        outcome=outcome,
        metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )
