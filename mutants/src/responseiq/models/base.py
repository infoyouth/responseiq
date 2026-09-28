# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Core SQLModel database models.

Defines the ``Log`` and ``Incident`` tables that back the FastAPI
endpoints and the remediation pipeline. All timestamps are UTC-aware;
``FeedbackRecord`` and ``IncidentEmbedding`` are co-located here to
keep the schema in one place.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _now():
    return datetime.now(timezone.utc)


class Log(SQLModel, table=True):  # type: ignore[call-arg]
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    message: str
    timestamp: datetime = Field(default_factory=_now)
    severity: str | None = None


class Incident(SQLModel, table=True):  # type: ignore[call-arg]
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    log_id: int
    detected_at: datetime = Field(default_factory=_now)
    severity: str | None = None
    description: str | None = None
    source: str | None = Field(default="unknown", description="detection source: ai or rules")


class FeedbackRecord(SQLModel, table=True):  # type: ignore[call-arg]
    """P-F1: Human approval/rejection of a suggested remediation."""

    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    log_id: int = Field(index=True)
    approved: bool
    comment: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_now)


class IncidentEmbedding(SQLModel, table=True):  # type: ignore[call-arg]
    """P-F2: Text embedding for semantic incident deduplication.

    ``embedding_json`` stores a JSON-encoded list[float] (1536 dims for
    text-embedding-3-small).  This is SQLite + Postgres compatible today.
    A pgvector VECTOR(1536) column can replace it in future without changing
    the service layer.
    """

    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    incident_id: int = Field(index=True, unique=True)
    log_id: int = Field(index=True)
    embedding_json: str = Field(description="JSON-encoded float array.")
    model: str = Field(default="text-embedding-3-small")
    created_at: datetime = Field(default_factory=_now)


class ProofBundleRecord(SQLModel, table=True):  # type: ignore[call-arg]
    """#2 v2.18.0: Persistent SOC2-ready audit record for a sealed ProofBundle.

    Written by ``proof_persistence_service.persist_proof_bundle()`` immediately
    after ``ProofBundle.seal_forensic_evidence()`` finalises the post-fix chain.
    Readable via ``GET /api/v1/incidents/{incident_id}/proof``.

    Fields mirror the ``EvidenceIntegrity`` snapshot so the record is fully
    self-contained and does not require the in-memory ProofBundle to be present.
    """

    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    incident_id: str = Field(index=True, description="String incident identifier (uuid or slug)")
    # Cryptographic integrity fields (copied from EvidenceIntegrity)
    integrity_hash: Optional[str] = Field(default=None, description="SHA-256 hex of evidence payload")
    chain_hash: Optional[str] = Field(default=None, description="SHA-256(integrity_hash + prev_hash)")
    algorithm: str = Field(default="SHA-256")
    sealed_at: Optional[datetime] = Field(default=None, description="When ProofBundle.seal_forensic_evidence() ran")
    pre_fix_hash: Optional[str] = Field(default=None, description="SHA-256 of pre-fix test output")
    post_fix_hash: Optional[str] = Field(default=None, description="SHA-256 of post-fix validation output")
    chain_verified: bool = Field(default=False)
    tamper_proof: bool = Field(default=False)
    # Confidence scores from the ProofBundle
    reproduction_confidence: float = Field(default=0.0)
    fix_confidence: float = Field(default=0.0)
    # Record housekeeping
    created_at: datetime = Field(default_factory=_now)


class AuditEventLog(SQLModel, table=True):  # type: ignore[call-arg]
    """SOC2 CC6/CC7: Immutable, append-only audit event log.

    Records every significant action across the ResponseIQ pipeline —
    Trust Gate decisions, HMAC failures, PR interventions, rollbacks,
    human feedback, and proof sealing. Written by
    ``audit_service.log_event()``; never updated or deleted in-process.

    Browsable via ``GET /api/v1/audit/events`` with date-range,
    event_type, incident_id, and outcome filters.
    """

    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    # Event identity
    event_type: str = Field(index=True, description="AuditEventType value e.g. 'trust_gate.passed'")
    incident_id: Optional[str] = Field(default=None, index=True, description="Related incident identifier (if any)")
    # Actor: 'system', 'user:<id>', 'bot', 'webhook:datadog', etc.
    actor: str = Field(default="system", description="Who/what generated this event")
    # Outcome: success | blocked | warned | failed
    outcome: str = Field(default="success", description="Event outcome: success, blocked, warned, failed")
    # Human-readable summary
    action: str = Field(description="One-line human-readable description of what happened")
    # Supplementary detail (JSON-encoded dict — optional)
    metadata_json: Optional[str] = Field(default=None, description="JSON blob with event-specific detail")
    # Request context (best-effort; not always available from background tasks)
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    # Record housekeeping
    timestamp: datetime = Field(default_factory=_now, index=True)


class WatchdogRecord(SQLModel, table=True):  # type: ignore[call-arg]
    """#3 v2.18.0: Audit record for each post-apply watchdog run.

    Written by ``WatchdogService`` when a monitoring window concludes,
    whether or not the rollback threshold was breached.
    """

    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    incident_id: str = Field(index=True)
    triggered: bool = Field(default=False, description="True if error-rate threshold was breached")
    reason: Optional[str] = Field(default=None)
    error_rate_observed: float = Field(default=0.0, description="Peak error rate during window")
    error_threshold: float = Field(default=0.05)
    window_seconds: int = Field(default=300)
    rollback_script_path: Optional[str] = Field(default=None)
    started_at: datetime = Field(default_factory=_now)
    completed_at: Optional[datetime] = Field(default=None)
