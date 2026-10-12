# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Typed, provenance-aware remediation outcome records."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OutcomeSource(str, Enum):
    HUMAN_REVIEW = "human_review"
    SYNTHETIC_REPLAY = "synthetic_replay"
    OFFICIAL_SWEBENCH = "official_swebench"
    CUSTOMER_APPROVED = "customer_approved"


class OutcomeStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FIXED = "fixed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    UNKNOWN = "unknown"


class OutcomeLedgerEntry(BaseModel):
    """Immutable outcome measurements; unknown values stay unknown, never inferred."""

    model_config = ConfigDict(frozen=True)

    incident_id: str = Field(min_length=1, max_length=200)
    source: OutcomeSource
    status: OutcomeStatus
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dataset_name: Optional[str] = Field(default=None, max_length=200)
    dataset_revision: Optional[str] = Field(default=None, max_length=200)
    case_id: Optional[str] = Field(default=None, max_length=200)
    repository_commit: Optional[str] = Field(default=None, max_length=64)
    model_name: Optional[str] = Field(default=None, max_length=200)
    root_cause_correct: Optional[bool] = None
    patch_applied: Optional[bool] = None
    validation_passed: Optional[bool] = None
    rollback_succeeded: Optional[bool] = None
    review_duration_seconds: Optional[float] = Field(default=None, ge=0)
    duration_ms: Optional[float] = Field(default=None, ge=0)
    cost_usd: Optional[float] = Field(default=None, ge=0)
    evidence_level: Optional[str] = Field(default=None, max_length=64)
    evidence_completeness: Optional[float] = Field(default=None, ge=0, le=1)
