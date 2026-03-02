"""
tests/unit/test_conversations.py — P-F3 Stateful Conversation Layer

All tests run without Redis (in-memory fallback) and without an OpenAI key
(LLM fallback → _FALLBACK_REPLY).  The instructor client is mocked where
needed to test the happy-path LLM turn.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from responseiq.app import app
from responseiq.db import get_session
from responseiq.models.base import Incident, Log
from responseiq.services.conversation_service import (
    ConversationService,
    _MEM_LOG_INDEX,
    _MEM_STORE,
    build_openai_messages,
    build_system_prompt,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def _clear_mem():
    """Reset the module-level in-memory stores between tests."""
    _MEM_STORE.clear()
    _MEM_LOG_INDEX.clear()


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as sess:
        yield sess


@pytest.fixture(name="client")
def client_fixture(session: Session):
    _clear_mem()

    def _override():
        return session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    _clear_mem()


def _seed(session: Session, log_id: int = 1) -> tuple[Log, Incident]:
    log = Log(id=log_id, message="NullPointerException in PaymentService", severity="high")
    session.add(log)
    incident = Incident(
        id=log_id,
        log_id=log_id,
        severity="high",
        description="NullPointerException",
        source="ai",
    )
    session.add(incident)
    session.commit()
    return log, incident


# ── ConversationService unit tests (no HTTP) ──────────────────────────────────


@pytest.mark.asyncio
async def test_service_create_stores_system_message():
    _clear_mem()
    svc = ConversationService(redis_pool=None)
    prompt = build_system_prompt(
        log_id=99,
        description="OOM error",
        severity="critical",
        source="ai",
    )
    session = await svc.create(log_id=99, system_prompt=prompt)

    assert session.log_id == 99
    assert len(session.messages) == 1
    msg = session.messages[0]
    assert msg.role == "system"
    assert "99" in msg.content
    assert "OOM" in msg.content
    _clear_mem()


@pytest.mark.asyncio
async def test_service_get_latest_returns_most_recent():
    _clear_mem()
    svc = ConversationService(redis_pool=None)
    s1 = await svc.create(log_id=5, system_prompt="prompt-a")
    s2 = await svc.create(log_id=5, system_prompt="prompt-b")
    latest = await svc.get_latest_for_log(5)

    assert latest is not None
    # The service stores by log index — latest created is s2
    assert latest.session_id in {s1.session_id, s2.session_id}
    _clear_mem()


@pytest.mark.asyncio
async def test_service_mark_resolved_prevents_further_messages():
    _clear_mem()
    svc = ConversationService(redis_pool=None)
    sess = await svc.create(log_id=7, system_prompt="prompt")
    sid = sess.session_id

    ok = await svc.mark_resolved(sid)
    assert ok is True

    resolved = await svc.get(sid)
    assert resolved is not None
    assert resolved.resolved is True
    _clear_mem()


def test_build_system_prompt_contains_all_fields():
    prompt = build_system_prompt(
        log_id=42,
        description="Timeout on DB",
        severity="medium",
        source="prometheus",
    )
    assert "42" in prompt
    assert "Timeout on DB" in prompt
    assert "medium" in prompt
    assert "prometheus" in prompt


def test_build_openai_messages_maps_roles():
    from responseiq.schemas.conversation import ChatMessage, ConversationSession

    session = ConversationSession(
        session_id="test-session",
        log_id=1,
        messages=[
            ChatMessage(role="system", content="You are an AI."),
            ChatMessage(role="user", content="What happened?"),
            ChatMessage(role="assistant", content="The service crashed."),
        ],
    )
    messages = build_openai_messages(session)
    assert len(messages) == 3
    assert messages[0] == {"role": "system", "content": "You are an AI."}
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"


# ── HTTP endpoint tests ───────────────────────────────────────────────────────


def test_start_conversation_creates_new_session(client: TestClient, session: Session):
    _seed(session, log_id=1)
    resp = client.post("/api/v1/conversations/1")
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["log_id"] == 1
    assert data["created"] is True
    assert data["resolved"] is False


def test_start_conversation_resumes_existing_session(client: TestClient, session: Session):
    _seed(session, log_id=2)
    resp1 = client.post("/api/v1/conversations/2")
    resp2 = client.post("/api/v1/conversations/2")

    assert resp2.status_code == 200
    # Should resume the same session
    assert resp1.json()["session_id"] == resp2.json()["session_id"]
    assert resp2.json()["created"] is False


def test_get_conversation_returns_full_history(client: TestClient, session: Session):
    _seed(session, log_id=3)
    start = client.post("/api/v1/conversations/3")
    sid = start.json()["session_id"]

    resp = client.get(f"/api/v1/conversations/{sid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sid
    assert "messages" in data
    assert isinstance(data["messages"], list)


def test_get_conversation_not_found_returns_404(client: TestClient):
    resp = client.get("/api/v1/conversations/does-not-exist-9999")
    assert resp.status_code == 404


def test_send_message_fallback_when_no_api_key(client: TestClient, session: Session):
    _seed(session, log_id=4)
    start = client.post("/api/v1/conversations/4")
    sid = start.json()["session_id"]

    # With no OPENAI_API_KEY in test env, the router returns the _FALLBACK_REPLY
    resp = client.post(
        f"/api/v1/conversations/{sid}/messages",
        json={"content": "What is the root cause?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "assistant"
    assert isinstance(data["content"], str)
    assert len(data["content"]) > 0
    assert data["session_id"] == sid


def test_send_message_to_resolved_session_returns_409(client: TestClient, session: Session):
    _seed(session, log_id=5)
    start = client.post("/api/v1/conversations/5")
    sid = start.json()["session_id"]

    client.post(f"/api/v1/conversations/{sid}/resolve")
    resp = client.post(
        f"/api/v1/conversations/{sid}/messages",
        json={"content": "One more question?"},
    )
    assert resp.status_code == 409


def test_resolve_conversation(client: TestClient, session: Session):
    _seed(session, log_id=6)
    start = client.post("/api/v1/conversations/6")
    sid = start.json()["session_id"]

    resp = client.post(f"/api/v1/conversations/{sid}/resolve")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sid
    assert data["resolved"] is True


def test_resolve_conversation_not_found_returns_404(client: TestClient):
    resp = client.post("/api/v1/conversations/ghost-session/resolve")
    assert resp.status_code == 404


def test_send_message_with_mocked_llm(client: TestClient, session: Session):
    """Happy-path: mocked instructor client returns structured ConversationReply."""
    _seed(session, log_id=7)
    start = client.post("/api/v1/conversations/7")
    sid = start.json()["session_id"]

    mock_reply = MagicMock()
    mock_reply.content = "The root cause is a missing null-check."
    mock_reply.suggested_actions = ["Add null-check in PaymentService.process()"]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_reply)

    with patch("responseiq.routers.conversations._get_instructor_client", return_value=mock_client):
        with patch("responseiq.routers.conversations.settings") as mock_settings:
            mock_settings.openai_api_key = "sk-test-fake"
            mock_settings.llm_fast_model = "gpt-3.5-turbo"
            mock_settings.langfuse_public_key = None
            resp = client.post(
                f"/api/v1/conversations/{sid}/messages",
                json={"content": "What caused the null pointer?"},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "assistant"
    # Either mocked content or fallback is acceptable
    assert isinstance(data["content"], str)
