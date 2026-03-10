# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Webhook ingestion payload schemas.

Pydantic models for the three supported webhook sources — Datadog,
PagerDuty, and Sentry — plus the canonical ``WebhookIncident`` that
each normaliser produces for the downstream remediation pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Source-specific payload models
# ---------------------------------------------------------------------------


class DatadogWebhookPayload(BaseModel):
    """
    Datadog Monitor webhook format.

    Datadog sends these fields when a monitor alert fires or resolves.
    Field names intentionally match the Datadog macro variable names.
    """

    id: Optional[str] = None
    title: Optional[str] = Field(default="", alias="msg_title")
    msg_title: Optional[str] = None
    msg_text: Optional[str] = None
    alert_type: Optional[str] = None  # info | warning | error | success
    priority: Optional[str] = None  # P1 … P5
    severity: Optional[str] = None  # mirrors priority when set
    body: Optional[str] = None
    source: Optional[str] = "datadog"
    tags: Optional[str] = None  # comma-separated tag string
    org_name: Optional[str] = None

    model_config = {"populate_by_name": True}


class PagerDutyEventData(BaseModel):
    """Inner ``event.data`` block of a PagerDuty v3 webhook."""

    id: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None  # triggered | acknowledged | resolved
    urgency: Optional[str] = None  # high | low
    body: Optional[Dict[str, Any]] = Field(default_factory=dict)
    service: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PagerDutyEvent(BaseModel):
    """Top-level ``event`` object in a PagerDuty v3 webhook."""

    id: Optional[str] = None
    event_type: Optional[str] = None  # incident.triggered | incident.resolved …
    resource_type: Optional[str] = None
    data: PagerDutyEventData = Field(default_factory=PagerDutyEventData)


class PagerDutyWebhookPayload(BaseModel):
    """PagerDuty v3 generic webhook envelope."""

    event: PagerDutyEvent = Field(default_factory=PagerDutyEvent)


class SentryIssue(BaseModel):
    """``data.issue`` block of a Sentry webhook."""

    id: Optional[str] = None
    title: Optional[str] = None
    level: Optional[str] = None  # fatal | error | warning | info | debug
    culprit: Optional[str] = None  # e.g. "app/views.py in my_view"
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SentryWebhookPayload(BaseModel):
    """Sentry issue webhook body (action: created / resolved / assigned)."""

    action: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)
    installation: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Normalised internal representation
# ---------------------------------------------------------------------------


class WebhookIncident(BaseModel):
    """
    Canonical incident produced by each normaliser.

    This is the single schema that ``POST /webhooks/*`` endpoints hand off to
    the ingestion pipeline — regardless of the originating source.
    """

    source: str  # "datadog" | "pagerduty" | "sentry"
    title: str
    severity: str  # low | medium | high | critical
    log_content: str  # combined log/body text forwarded to LLM
    idempotency_key: str  # sha256 fingerprint — used to deduplicate
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# HTTP response schema
# ---------------------------------------------------------------------------


class WebhookAck(BaseModel):
    """Response returned to the webhook sender on acceptance."""

    accepted: bool
    log_id: Optional[int] = None  # DB log row id (useful for SSE poll)
    message: str
    idempotency_key: str
    duplicate: bool = False  # True when the same event was seen before


class SSEEvent(BaseModel):
    """Single Server-Sent Event payload (JSON-encoded in the ``data:`` field)."""

    log_id: int
    status: str  # processing | complete | not_found | timeout
    incident_id: Optional[int] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
