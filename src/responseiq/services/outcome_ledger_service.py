# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Append-only outcome ledger backed by the audit event store."""

from __future__ import annotations

from responseiq.schemas.outcome import OutcomeLedgerEntry
from responseiq.services.audit_service import AuditEventType, log_event_sync


def record_outcome(entry: OutcomeLedgerEntry) -> bool:
    """Append a structured outcome event without storing incident or patch content."""
    record = log_event_sync(
        AuditEventType.REMEDIATION_OUTCOME_RECORDED,
        f"Remediation outcome recorded: {entry.status.value} ({entry.source.value})",
        incident_id=entry.incident_id,
        actor=entry.source.value,
        outcome=entry.status.value,
        metadata=entry.model_dump(mode="json"),
    )
    return record is not None
