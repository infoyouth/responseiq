"""
src/responseiq/schemas/feedback.py

Request/response schemas for the human feedback API (P-F1).

Engineers call POST /api/v1/feedback after reviewing a suggested
remediation.  Each approval or rejection is:
  1. Persisted to the FeedbackRecord DB table for audit.
  2. Passed to the Langfuse Scores API to label the associated
     LLM generation span — building the eval flywheel.
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
