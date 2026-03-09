# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Stateful multi-turn conversation router.

Exposes three endpoints for the AI conversation layer: start or resume
a session (``POST /{log_id}``), append a message and get a reply
(``POST /{session_id}/messages``), and retrieve the full session state
(``GET /{session_id}``). Sessions are Redis-backed in production.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from responseiq.ai.llm_service import _get_instructor_client
from responseiq.config.settings import settings
from responseiq.db import get_session
from responseiq.models.base import Incident, Log
from responseiq.schemas.conversation import (
    ConversationOut,
    ConversationReply,
    ConversationStartOut,
    MessageIn,
    MessageOut,
)
from responseiq.services.conversation_service import (
    ConversationService,
    build_openai_messages,
    build_system_prompt,
)
from responseiq.utils.logger import logger
from responseiq.utils.tracing import get_langfuse

router = APIRouter(prefix="/api/v1", tags=["conversations"])

_CONVERSATION_SYSTEM_SUPPLEMENT = (
    "You are a helpful, expert SRE assistant. Answer concisely. "
    "For 'suggested_actions' output up to 3 concrete next steps the engineer can take."
)

_FALLBACK_REPLY = (
    "AI analysis is currently unavailable (no OpenAI API key configured). "
    "Please check the incident details directly via GET /incidents."
)


def _get_svc(request: Request) -> ConversationService:
    pool = getattr(request.app.state, "arq_pool", None)
    return ConversationService(redis_pool=pool)


def _get_incident_context(log_id: int, db_session) -> tuple[str, str, str]:
    """Return (description, severity, source) for the incident associated with log_id."""
    incident = db_session.exec(__import__("sqlmodel").select(Incident).where(Incident.log_id == log_id)).first()
    if incident:
        return (
            incident.description or "No description available",
            incident.severity or "unknown",
            incident.source or "unknown",
        )
    # Fall back to the log message if incident not yet created
    log = db_session.get(Log, log_id)
    if log:
        return log.message[:200], log.severity or "unknown", "log"
    return "Incident not found", "unknown", "unknown"


# ── POST /api/v1/conversations/{log_id} ──────────────────────────────────────


@router.post(
    "/conversations/{log_id}",
    response_model=ConversationStartOut,
    status_code=200,
    summary="Start or resume a conversation about a log/incident",
)
async def start_or_resume_conversation(
    log_id: int,
    request: Request,
    db_session=Depends(get_session),
):
    """
    Start a new conversation or resume the most recent open session for
    ``log_id``.  The system message is automatically populated with the
    incident context (description, severity, source).
    """
    svc = _get_svc(request)

    # Try to resume latest open session first
    existing = await svc.get_latest_for_log(log_id)
    if existing:
        return ConversationStartOut(
            session_id=existing.session_id,
            log_id=log_id,
            created=False,
            message_count=len(existing.messages),
            resolved=existing.resolved,
        )

    # Create new session with incident context as system message
    description, severity, source = _get_incident_context(log_id, db_session)
    system_prompt = build_system_prompt(
        log_id=log_id,
        description=description,
        severity=severity,
        source=source,
    )
    session = await svc.create(log_id=log_id, system_prompt=system_prompt)

    return ConversationStartOut(
        session_id=session.session_id,
        log_id=log_id,
        created=True,
        message_count=len(session.messages),
        resolved=False,
    )


# ── POST /api/v1/conversations/{session_id}/messages ─────────────────────────


@router.post(
    "/conversations/{session_id}/messages",
    response_model=MessageOut,
    status_code=200,
    summary="Send a message and get the AI response",
)
async def send_message(
    session_id: str,
    payload: MessageIn,
    request: Request,
):
    """
    Append a user message to the session and run an LLM turn.

    - Full message history is passed to the model (context-aware responses).
    - Returns a structured ``MessageOut`` with ``content`` and ``suggested_actions``.
    - Returns 404 if session not found, 409 if session is resolved.
    """
    svc = _get_svc(request)

    session = await svc.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found or expired.")

    if session.resolved:
        raise HTTPException(
            status_code=409,
            detail="This session is resolved. Start a new conversation via POST /api/v1/conversations/{log_id}.",
        )

    # Append user message
    session = await svc.append_user_message(session_id, payload.content)
    if session is None:
        raise HTTPException(status_code=404, detail="Session disappeared during message append.")

    # Run LLM turn
    reply_content, suggested_actions = await _run_llm_turn(session_id, session)

    # Append assistant message
    await svc.append_assistant_message(session_id, reply_content)

    # Langfuse trace (no-op when not configured)
    _trace_conversation_turn(session_id, session.log_id, payload.content, reply_content)

    return MessageOut(
        session_id=session_id,
        content=reply_content,
        timestamp=datetime.now(timezone.utc),
        suggested_actions=suggested_actions,
    )


# ── GET /api/v1/conversations/{session_id} ────────────────────────────────────


@router.get(
    "/conversations/{session_id}",
    response_model=ConversationOut,
    summary="Get conversation session state",
)
async def get_conversation(session_id: str, request: Request):
    """Return the full session including all messages."""
    svc = _get_svc(request)
    session = await svc.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found or expired.")
    return ConversationOut(
        session_id=session.session_id,
        log_id=session.log_id,
        messages=session.messages,
        resolved=session.resolved,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


# ── POST /api/v1/conversations/{session_id}/resolve ──────────────────────────


@router.post(
    "/conversations/{session_id}/resolve",
    status_code=200,
    summary="Mark a conversation as resolved",
)
async def resolve_conversation(session_id: str, request: Request):
    """
    Mark the session as resolved.  Subsequent message posts will return 409.
    """
    svc = _get_svc(request)
    ok = await svc.mark_resolved(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found.")
    return {"session_id": session_id, "resolved": True}


# ── helpers ───────────────────────────────────────────────────────────────────


async def _run_llm_turn(session_id: str, session) -> tuple[str, list[str]]:
    """Call the LLM with full history. Returns (content, suggested_actions)."""
    api_key = settings.openai_api_key
    if not api_key:
        logger.warning("ConversationRouter: OpenAI not configured — returning fallback reply.")
        return _FALLBACK_REPLY, []

    try:
        messages = build_openai_messages(session)
        client = _get_instructor_client()
        result: ConversationReply = await client.chat.completions.create(
            model=settings.llm_fast_model,
            response_model=ConversationReply,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.3,
            max_tokens=800,
        )
        return result.content, result.suggested_actions
    except Exception as exc:
        logger.warning("ConversationRouter: LLM turn failed for session %s: %s", session_id, exc)
        return f"AI response unavailable: {exc}", []


def _trace_conversation_turn(session_id: str, log_id: int, user_content: str, reply_content: str) -> None:
    lf = get_langfuse()
    if lf is None:
        return
    try:
        gen = lf.start_generation(
            name="conversation_turn",
            model=settings.llm_fast_model,
            input=[{"role": "user", "content": user_content}],
            metadata={"session_id": session_id, "log_id": log_id},
        )
        gen.update(output=reply_content[:300])
        gen.end()
    except Exception as exc:  # pragma: no cover
        logger.debug("Langfuse conversation trace failed (non-fatal): %s", exc)
