# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Normalized telemetry context carried into incident analysis."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OTelIncidentContext(BaseModel):
    """Identity and trace fields extracted from one OpenTelemetry log record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    service_name: str | None = None
    deployment_environment_name: str | None = None
    deployment_id: str | None = None
    observed_at: datetime | None = None
    trace_id: str | None = None
    span_id: str | None = None
    provenance: dict[str, str] = Field(default_factory=dict)


class ParsedOTelLogRecord(BaseModel):
    """A log body plus normalized context from one OTel JSONL record."""

    body: str
    context: OTelIncidentContext
