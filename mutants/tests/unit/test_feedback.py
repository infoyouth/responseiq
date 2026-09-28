"""tests/unit/test_feedback.py — P-F1 Human Feedback Loop"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from responseiq.app import app
from responseiq.db import get_session
from responseiq.models.base import FeedbackRecord, Incident, Log


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def _get_session_override():
        return session

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_log_and_incident(session: Session, log_id_override: int = 1) -> tuple[Log, Incident]:
    log = Log(id=log_id_override, message="NullPointerException in service", severity="high")
    session.add(log)
    incident = Incident(
        id=log_id_override,
        log_id=log_id_override,
        severity="high",
        description="NullPointerException",
        source="ai",
    )
    session.add(incident)
    session.commit()
    return log, incident


# ── POST /api/v1/feedback ─────────────────────────────────────────────────────


def test_submit_feedback_approved(client: TestClient, session: Session):
    _seed_log_and_incident(session, log_id_override=10)
    with patch("responseiq.routers.feedback.score_langfuse") as mock_score:
        resp = client.post("/api/v1/feedback", json={"log_id": 10, "approved": True})

    assert resp.status_code == 201
    data = resp.json()
    assert data["log_id"] == 10
    assert data["approved"] is True
    assert data["comment"] is None
    assert "id" in data
    assert "created_at" in data
    mock_score.assert_called_once_with(
        trace_name="log_10",
        score_name="human_approval",
        value=1.0,
        comment=None,
    )


def test_submit_feedback_rejected_with_comment(client: TestClient, session: Session):
    _seed_log_and_incident(session, log_id_override=11)
    with patch("responseiq.routers.feedback.score_langfuse"):
        resp = client.post(
            "/api/v1/feedback",
            json={"log_id": 11, "approved": False, "comment": "Wrong root cause identified"},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["approved"] is False
    assert data["comment"] == "Wrong root cause identified"


def test_submit_feedback_score_value_for_rejection(client: TestClient, session: Session):
    """Rejected feedback must pass score value 0.0 to Langfuse."""
    _seed_log_and_incident(session, log_id_override=12)
    with patch("responseiq.routers.feedback.score_langfuse") as mock_score:
        client.post("/api/v1/feedback", json={"log_id": 12, "approved": False})

    mock_score.assert_called_once()
    assert mock_score.call_args.kwargs["value"] == 0.0


def test_submit_feedback_persisted_to_db(client: TestClient, session: Session):
    """FeedbackRecord must actually be written to the DB."""
    _seed_log_and_incident(session, log_id_override=13)
    with patch("responseiq.routers.feedback.score_langfuse"):
        client.post("/api/v1/feedback", json={"log_id": 13, "approved": True})

    records = session.exec(__import__("sqlmodel").select(FeedbackRecord).where(FeedbackRecord.log_id == 13)).all()
    assert len(records) == 1
    assert records[0].approved is True


def test_submit_multiple_feedback_idempotent(client: TestClient, session: Session):
    """Multiple feedback entries for the same log_id are all persisted (not deduplicated)."""
    _seed_log_and_incident(session, log_id_override=14)
    with patch("responseiq.routers.feedback.score_langfuse"):
        client.post("/api/v1/feedback", json={"log_id": 14, "approved": True})
        client.post("/api/v1/feedback", json={"log_id": 14, "approved": False})

    records = session.exec(__import__("sqlmodel").select(FeedbackRecord).where(FeedbackRecord.log_id == 14)).all()
    assert len(records) == 2


# ── GET /api/v1/feedback/{log_id} ────────────────────────────────────────────


def test_get_feedback_summary(client: TestClient, session: Session):
    _seed_log_and_incident(session, log_id_override=20)
    now = datetime.now(timezone.utc)
    session.add(FeedbackRecord(log_id=20, approved=True, created_at=now))
    session.add(FeedbackRecord(log_id=20, approved=True, created_at=now))
    session.add(FeedbackRecord(log_id=20, approved=False, created_at=now))
    session.commit()

    resp = client.get("/api/v1/feedback/20")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["approvals"] == 2
    assert data["rejections"] == 1
    assert abs(data["acceptance_rate"] - 0.6667) < 0.001


def test_get_feedback_summary_not_found(client: TestClient, session: Session):
    resp = client.get("/api/v1/feedback/9999")
    assert resp.status_code == 404


def test_get_feedback_acceptance_rate_all_approved(client: TestClient, session: Session):
    _seed_log_and_incident(session, log_id_override=21)
    now = datetime.now(timezone.utc)
    for _ in range(5):
        session.add(FeedbackRecord(log_id=21, approved=True, created_at=now))
    session.commit()

    resp = client.get("/api/v1/feedback/21")
    data = resp.json()
    assert data["acceptance_rate"] == 1.0
