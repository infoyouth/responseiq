# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Request/response schemas for the stateful conversation layer.

Each conversation is tied to a ``log_id`` and stores a rolling message
history in Redis keyed by ``session_id`` (UUID4). The first message is
always a system prompt grounding the AI in the incident context.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Literal

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=_utcnow)


class ConversationSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    log_id: int
    messages: List[ChatMessage] = Field(default_factory=list)
    resolved: bool = False
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    ttl_seconds: int = Field(default=86400, description="Session TTL in seconds (24h).")


class MessageIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class ConversationReply(BaseModel):
    """Structured LLM response — returned via instructor."""

    content: str = Field(..., min_length=1)
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="Up to 5 follow-up actions the engineer can take.",
    )


class MessageOut(BaseModel):
    session_id: str
    role: Literal["assistant"] = "assistant"
    content: str
    timestamp: datetime
    suggested_actions: List[str] = Field(default_factory=list)


class ConversationOut(BaseModel):
    session_id: str
    log_id: int
    messages: List[ChatMessage]
    resolved: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationStartOut(BaseModel):
    """Returned from POST /api/v1/conversations/{log_id}."""

    session_id: str
    log_id: int
    created: bool = Field(description="True = new session, False = resumed existing.")
    message_count: int
    resolved: bool
