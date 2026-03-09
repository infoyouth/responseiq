# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Request/response schemas for the human feedback API.

Engineers submit an approval or rejection after reviewing a suggested
remediation. Each response is persisted to ``FeedbackRecord`` for audit
and passed to the Langfuse Scores API to label the LLM trace, building
the evaluation flywheel over time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class FeedbackIn(BaseModel):
    log_id: int = Field(..., description="ID of the Log row this feedback targets.")
    approved: bool = Field(..., description="True = engineer accepted the fix. False = rejected.")
    comment: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional human note explaining the decision.",
    )


class FeedbackOut(BaseModel):
    id: int
    log_id: int
    approved: bool
    comment: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackSummary(BaseModel):
    """Aggregated feedback stats for a given log_id."""

    log_id: int
    total: int
    approvals: int
    rejections: int
    acceptance_rate: float = Field(description="Fraction of approved feedback records (0.0–1.0).")
    last_feedback_at: Optional[datetime] = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
