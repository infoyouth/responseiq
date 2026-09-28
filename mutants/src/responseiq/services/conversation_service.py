# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Redis-backed stateful AI conversation sessions.

Each conversation is scoped to a ``log_id`` and stores all message turns
in Redis as a JSON-encoded ``ConversationSession`` with a 24h TTL.
Degrades gracefully to an in-memory dict when Redis is unavailable,
so unit tests work with zero external dependencies.
"""

from __future__ import annotations
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

from responseiq.schemas.conversation import (
    ChatMessage,
    ConversationSession,
)
from responseiq.utils.logger import logger

# ── in-memory fallback store (used when Redis pool is None) ──────────────────
_MEM_STORE: dict[str, str] = {}
_MEM_LOG_INDEX: dict[str, list[str]] = {}

_KEY_PREFIX = "responseiq:conv:"
_SESSION_KEY = _KEY_PREFIX + "{sid}"
_LOG_IDX_KEY = _KEY_PREFIX + "log:{lid}:sessions"

_SYSTEM_PROMPT_TMPL = (
    "You are ResponseIQ's AI assistant analysing incident log_id={log_id}.\n"
    "Incident: {description} (severity: {severity}, source: {source}).\n"
    "Answer questions about the incident, proposed fixes, and provide actionable "
    "guidance. Be concise, technical, and precise. When suggesting actions, "
    "output them as the ``suggested_actions`` list."
)


def _session_key(session_id: str) -> str:
    return _SESSION_KEY.format(sid=session_id)


def _log_idx_key(log_id: int) -> str:
    return _LOG_IDX_KEY.format(lid=log_id)


class ConversationService:
    """
    CRUD + message-append service for ConversationSession objects.

    Parameters
    ----------
    redis_pool :
        An ``arq.ArqRedis`` / ``redis.asyncio.Redis`` instance wired in from
        ``app.state.arq_pool``.  Pass ``None`` (default) to use the in-process
        fallback dict (suitable for tests).
    """

    def __init__(self, redis_pool: Optional[Any] = None) -> None:
        self._pool = redis_pool

    # ── helpers ───────────────────────────────────────────────────────────────

    async def _get_raw(self, key: str) -> Optional[str]:
        if self._pool is not None:
            val = await self._pool.get(key)
            return val.decode() if isinstance(val, bytes) else val
        return _MEM_STORE.get(key)

    async def _set_raw(self, key: str, value: str, ttl: int) -> None:
        if self._pool is not None:
            await self._pool.set(key, value, ex=ttl)
        else:
            _MEM_STORE[key] = value

    async def _lpush(self, key: str, value: str) -> None:
        if self._pool is not None:
            await self._pool.lpush(key, value)
        else:
            _MEM_LOG_INDEX.setdefault(key, []).insert(0, value)

    async def _lrange(self, key: str) -> list[str]:
        if self._pool is not None:
            items = await self._pool.lrange(key, 0, -1)
            return [i.decode() if isinstance(i, bytes) else i for i in items]
        return _MEM_LOG_INDEX.get(key, [])

    # ── public API ────────────────────────────────────────────────────────────

    async def get(self, session_id: str) -> Optional[ConversationSession]:
        """Return a ConversationSession by its ID, or None if not found / expired."""
        raw = await self._get_raw(_session_key(session_id))
        if raw is None:
            return None
        try:
            return ConversationSession.model_validate_json(raw)
        except Exception as exc:
            logger.warning("ConversationService: corrupt session %s: %s", session_id, exc)
            return None

    async def save(self, session: ConversationSession) -> None:
        """Persist (create or overwrite) a session."""
        session.updated_at = datetime.now(timezone.utc)
        await self._set_raw(
            _session_key(session.session_id),
            session.model_dump_json(),
            session.ttl_seconds,
        )

    async def create(
        self,
        log_id: int,
        system_prompt: str,
    ) -> ConversationSession:
        """Create a new session with the system message and persist it."""
        session = ConversationSession(log_id=log_id)
        session.messages.append(ChatMessage(role="system", content=system_prompt))
        await self.save(session)
        await self._lpush(_log_idx_key(log_id), session.session_id)
        logger.info(
            "ConversationService: new session %s for log_id=%d",
            session.session_id,
            log_id,
        )
        return session

    async def get_latest_for_log(self, log_id: int) -> Optional[ConversationSession]:
        """Return the most recent non-resolved session for a log, or None."""
        ids = await self._lrange(_log_idx_key(log_id))
        for sid in ids:
            session = await self.get(sid)
            if session and not session.resolved:
                return session
        return None

    async def append_user_message(self, session_id: str, content: str) -> Optional[ConversationSession]:
        """Append a user message to a session and persist. Returns None if not found."""
        session = await self.get(session_id)
        if session is None:
            return None
        session.messages.append(ChatMessage(role="user", content=content))
        await self.save(session)
        return session

    async def append_assistant_message(self, session_id: str, content: str) -> Optional[ConversationSession]:
        """Append the AI response to a session and persist."""
        session = await self.get(session_id)
        if session is None:
            return None
        session.messages.append(ChatMessage(role="assistant", content=content))
        await self.save(session)
        return session

    async def mark_resolved(self, session_id: str) -> bool:
        """Mark a session as resolved (read-only). Returns False if not found."""
        session = await self.get(session_id)
        if session is None:
            return False
        session.resolved = True
        await self.save(session)
        return True


# ── LLM message builder ───────────────────────────────────────────────────────


def build_openai_messages(session: ConversationSession) -> List[dict]:
    """
    Convert a ConversationSession into the ``messages`` list expected by
    the OpenAI / instructor client.

    All message roles are mapped 1:1.  The system message is always first.
    """
    return [{"role": m.role, "content": m.content} for m in session.messages]


def build_system_prompt(
    log_id: int,
    description: str = "Unknown error",
    severity: str = "unknown",
    source: str = "unknown",
) -> str:
    return _SYSTEM_PROMPT_TMPL.format(
        log_id=log_id,
        description=description,
        severity=severity,
        source=source,
    )
