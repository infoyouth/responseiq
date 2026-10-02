"""Normalized operational change events used for incident correlation."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DeploymentEventKind(str, Enum):
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    DEPLOYMENT = "deployment"
    KUBERNETES_ROLLOUT = "kubernetes_rollout"
    IMAGE = "image"
    FEATURE_FLAG = "feature_flag"
    CONFIGURATION = "configuration"


class DeploymentEvent(BaseModel):
    """Provider-neutral event describing a code or runtime change."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    kind: DeploymentEventKind
    occurred_at: datetime
    source: str = Field(min_length=1)
    service: str | None = None
    commit_sha: str | None = None
    image_sha: str | None = None
    config_digest: str | None = None
    feature_flags: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @field_validator("service")
    @classmethod
    def normalize_service(cls, value: str | None) -> str | None:
        return value.strip().lower() or None if value is not None else None

    @field_validator("commit_sha", "image_sha", "config_digest")
    @classmethod
    def normalize_identifiers(cls, value: str | None) -> str | None:
        return value.strip().lower() or None if value is not None else None


class DeploymentCorrelationResult(BaseModel):
    """Evidence that an event is related in time/identity to an incident."""

    event: DeploymentEvent
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    relation: str = "correlated"
    lookback_hours: int = Field(gt=0)
