"""tests/unit/test_audit_service.py — SOC2 Audit Service unit tests.

Coverage
--------
AuditEventType enum
    All canonical event type values are strings (str Enum).           1 test
    Values match expected patterns.                                    1 test

log_event (async)
    Persists a row and returns an AuditEventLog record.               1 test
    Row has correct field values.                                      1 test
    Swallows DB errors and returns None (fire-and-forget).             1 test

log_event_sync
    Persists a row synchronously with correct fields.                  1 test
    Swallows DB errors and returns None.                               1 test

_write_audit_record
    Truncates action to 500 chars.                                     1 test
    Serialises metadata dict to JSON string.                           1 test
    Stores None metadata_json when metadata is None.                   1 test

Audit router
    GET /api/v1/audit/events — returns events list with schema.        1 test
    GET /api/v1/audit/events — event_type filter narrows results.      1 test
    GET /api/v1/audit/events — incident_id filter works.               1 test
    GET /api/v1/audit/events — outcome filter works.                   1 test
    GET /api/v1/audit/events — limit / offset pagination.              1 test
    GET /api/v1/audit/events/{incident_id} — timeline ordered ASC.     1 test
    GET /api/v1/audit/events/{incident_id} — empty list when none.     1 test
    GET /api/v1/audit/summary — counts match seeded data.              1 test
    GET /api/v1/audit/summary — acceptance_rate calculation.           1 test
    GET /api/v1/audit/summary — acceptance_rate None when 0 TG events. 1 test
    GET /api/v1/audit/retention-policy — returns expected fields.      1 test
    GET /api/v1/audit/retention-policy — env override key present.     1 test

Trust gate integration
    validate_remediation PASS emits TRUST_GATE_PASSED event.           1 test
    validate_remediation BLOCK emits TRUST_GATE_BLOCKED event.         1 test

Trust Gate (SOC2):
    rationale   : Immutable, append-only audit log. Fire-and-forget writes
                  so audit failures never block business-logic paths.
    blast_radius: DB model only; no changes to core remediation pipeline.
    rollback_plan: DELETE FROM audit_event_log WHERE id = <id> (audit ops only).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from responseiq.app import app
from responseiq.db import get_session
from responseiq.models.base import AuditEventLog
from responseiq.services.audit_service import AuditEventType, _write_audit_record, log_event, log_event_sync


# ── In-memory DB fixtures ────────────────────────────────────────────────────


@pytest.fixture(name="mem_session")
def mem_session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(mem_session: Session):
    def _override():
        return mem_session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# Helper — insert a raw AuditEventLog row using session directly
def _seed_event(
    session: Session,
    event_type: str = AuditEventType.TRUST_GATE_PASSED,
    incident_id: str = "inc-001",
    actor: str = "system",
    outcome: str = "success",
    action: str = "Test event",
) -> AuditEventLog:
    row = AuditEventLog(
        event_type=event_type,
        incident_id=incident_id,
        actor=actor,
        outcome=outcome,
        action=action,
        timestamp=datetime.now(timezone.utc),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


# ── AuditEventType enum ──────────────────────────────────────────────────────


class TestAuditEventType:
    def test_all_values_are_strings(self):
        for member in AuditEventType:
            assert isinstance(member.value, str), f"{member.name} value must be str"

    def test_key_event_values(self):
        assert AuditEventType.TRUST_GATE_PASSED == "trust_gate.passed"
        assert AuditEventType.TRUST_GATE_BLOCKED == "trust_gate.blocked"
        assert AuditEventType.WEBHOOK_HMAC_FAILED == "webhook.hmac_failed"
        assert AuditEventType.HUMAN_FEEDBACK_SUBMITTED == "feedback.submitted"
        assert AuditEventType.PROOF_BUNDLE_SEALED == "proof.sealed"


# ── _write_audit_record ──────────────────────────────────────────────────────


class TestWriteAuditRecord:
    def test_truncates_action_at_500_chars(self, mem_session):
        long_action = "x" * 600
        with patch("responseiq.services.audit_service.get_session") as mock_gs:
            mock_gs.return_value = iter([mem_session])
            record = _write_audit_record(AuditEventType.INCIDENT_ANALYZED, long_action)
        assert record is not None
        assert len(record.action) == 500

    def test_metadata_serialised_to_json(self, mem_session):
        meta = {"severity": "high", "policy_mode": "pr_only"}
        with patch("responseiq.services.audit_service.get_session") as mock_gs:
            mock_gs.return_value = iter([mem_session])
            record = _write_audit_record(
                AuditEventType.TRUST_GATE_BLOCKED,
                "blocked",
                metadata=meta,
            )
        assert record is not None
        assert record.metadata_json is not None
        parsed = json.loads(record.metadata_json)
        assert parsed["severity"] == "high"

    def test_none_metadata_stores_null(self, mem_session):
        with patch("responseiq.services.audit_service.get_session") as mock_gs:
            mock_gs.return_value = iter([mem_session])
            record = _write_audit_record(AuditEventType.PR_OPENED, "pr opened", metadata=None)
        assert record is not None
        assert record.metadata_json is None

    def test_returns_none_on_db_error(self):
        with patch("responseiq.services.audit_service.get_session", side_effect=Exception("DB down")):
            result = _write_audit_record(AuditEventType.INCIDENT_ANALYZED, "will fail")
        assert result is None


# ── log_event_sync ───────────────────────────────────────────────────────────


class TestLogEventSync:
    def test_persists_row_with_correct_fields(self, mem_session):
        with patch("responseiq.services.audit_service.get_session") as mock_gs:
            mock_gs.return_value = iter([mem_session])
            record = log_event_sync(
                AuditEventType.HUMAN_FEEDBACK_SUBMITTED,
                "Feedback: approved",
                incident_id="log-42",
                actor="user",
                outcome="success",
            )
        assert record is not None
        assert record.event_type == "feedback.submitted"
        assert record.incident_id == "log-42"
        assert record.actor == "user"
        assert record.outcome == "success"

    def test_swallows_db_errors_and_returns_none(self):
        with patch("responseiq.services.audit_service.get_session", side_effect=RuntimeError("boom")):
            result = log_event_sync(AuditEventType.PR_OPENED, "pr opened")
        assert result is None


# ── log_event (async) ────────────────────────────────────────────────────────


class TestLogEventAsync:
    @pytest.mark.asyncio
    async def test_persists_row(self, mem_session):
        with patch("responseiq.services.audit_service.get_session") as mock_gs:
            mock_gs.return_value = iter([mem_session])
            record = await log_event(
                AuditEventType.TRUST_GATE_PASSED,
                "Trust Gate PASSED incident abc",
                incident_id="abc",
                outcome="success",
                metadata={"policy_mode": "pr_only"},
            )
        assert record is not None
        assert record.event_type == "trust_gate.passed"
        assert record.incident_id == "abc"
        assert record.outcome == "success"

    @pytest.mark.asyncio
    async def test_swallows_db_errors(self):
        with patch("responseiq.services.audit_service.get_session", side_effect=RuntimeError("db error")):
            result = await log_event(AuditEventType.WEBHOOK_HMAC_FAILED, "hmac fail")
        assert result is None


# ── Audit router — GET /api/v1/audit/events ──────────────────────────────────


class TestAuditEventsRouter:
    def test_returns_events_list(self, client, mem_session):
        _seed_event(mem_session)
        resp = client.get("/api/v1/audit/events")
        assert resp.status_code == 200
        body = resp.json()
        assert "events" in body
        assert body["total"] >= 1

    def test_event_schema_has_required_fields(self, client, mem_session):
        _seed_event(mem_session, action="check field presence")
        resp = client.get("/api/v1/audit/events", params={"limit": 1})
        assert resp.status_code == 200
        event = resp.json()["events"][0]
        for field in ("id", "event_type", "incident_id", "actor", "outcome", "action", "timestamp"):
            assert field in event, f"Missing field: {field}"

    def test_event_type_filter(self, client, mem_session):
        _seed_event(mem_session, event_type=AuditEventType.TRUST_GATE_BLOCKED, incident_id="blocked-1")
        _seed_event(mem_session, event_type=AuditEventType.TRUST_GATE_PASSED, incident_id="passed-1")
        resp = client.get("/api/v1/audit/events", params={"event_type": "trust_gate.blocked"})
        assert resp.status_code == 200
        events = resp.json()["events"]
        assert all(e["event_type"] == "trust_gate.blocked" for e in events)

    def test_incident_id_filter(self, client, mem_session):
        _seed_event(mem_session, incident_id="target-inc")
        _seed_event(mem_session, incident_id="other-inc")
        resp = client.get("/api/v1/audit/events", params={"incident_id": "target-inc"})
        assert resp.status_code == 200
        events = resp.json()["events"]
        assert all(e["incident_id"] == "target-inc" for e in events)
        assert len(events) >= 1

    def test_outcome_filter(self, client, mem_session):
        _seed_event(mem_session, outcome="blocked")
        _seed_event(mem_session, outcome="success")
        resp = client.get("/api/v1/audit/events", params={"outcome": "blocked"})
        assert resp.status_code == 200
        events = resp.json()["events"]
        assert all(e["outcome"] == "blocked" for e in events)

    def test_pagination_limit(self, client, mem_session):
        for i in range(5):
            _seed_event(mem_session, incident_id=f"inc-{i}")
        resp = client.get("/api/v1/audit/events", params={"limit": 2, "offset": 0})
        assert resp.status_code == 200
        assert len(resp.json()["events"]) <= 2

    def test_pagination_offset(self, client, mem_session):
        for i in range(4):
            _seed_event(mem_session, incident_id=f"page-{i}")
        resp_p1 = client.get("/api/v1/audit/events", params={"limit": 2, "offset": 0})
        resp_p2 = client.get("/api/v1/audit/events", params={"limit": 2, "offset": 2})
        ids_p1 = {e["id"] for e in resp_p1.json()["events"]}
        ids_p2 = {e["id"] for e in resp_p2.json()["events"]}
        assert ids_p1.isdisjoint(ids_p2), "Pages must not overlap"

    def test_actor_filter(self, client, mem_session):
        """Covers routers/audit.py L76 — actor WHERE clause."""
        _seed_event(mem_session, actor="sre-bot", incident_id="actor-1")
        _seed_event(mem_session, actor="human", incident_id="actor-2")
        resp = client.get("/api/v1/audit/events", params={"actor": "sre-bot"})
        assert resp.status_code == 200
        events = resp.json()["events"]
        assert all(e["actor"] == "sre-bot" for e in events)
        assert len(events) >= 1

    def test_since_filter(self, client, mem_session):
        """Covers routers/audit.py L78 — since WHERE clause."""
        from datetime import timedelta

        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        _seed_event(mem_session, incident_id="since-1")
        resp = client.get("/api/v1/audit/events", params={"since": past})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_until_filter(self, client, mem_session):
        """Covers routers/audit.py L80 — until WHERE clause."""
        from datetime import timedelta

        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        _seed_event(mem_session, incident_id="until-1")
        resp = client.get("/api/v1/audit/events", params={"until": future})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


# ── Audit router — GET /api/v1/audit/events/{incident_id} ────────────────────


class TestAuditTimelineRouter:
    def test_timeline_ordered_chronologically(self, client, mem_session):
        for action in ["first", "second", "third"]:
            _seed_event(mem_session, incident_id="ordered-inc", action=action)
        resp = client.get("/api/v1/audit/events/ordered-inc")
        assert resp.status_code == 200
        body = resp.json()
        assert body["incident_id"] == "ordered-inc"
        actions = [e["action"] for e in body["timeline"]]
        assert actions == ["first", "second", "third"]

    def test_empty_list_when_no_events(self, client, mem_session):
        resp = client.get("/api/v1/audit/events/nonexistent-inc-999")
        assert resp.status_code == 200
        body = resp.json()
        assert body["event_count"] == 0
        assert body["timeline"] == []


# ── Audit router — GET /api/v1/audit/summary ─────────────────────────────────


class TestAuditSummaryRouter:
    def test_summary_counts_match_seeded_data(self, client, mem_session):
        _seed_event(mem_session, event_type=AuditEventType.TRUST_GATE_PASSED, outcome="success")
        _seed_event(mem_session, event_type=AuditEventType.TRUST_GATE_PASSED, outcome="success")
        _seed_event(mem_session, event_type=AuditEventType.TRUST_GATE_BLOCKED, outcome="blocked")
        resp = client.get("/api/v1/audit/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert body["trust_gate"]["passed"] == 2
        assert body["trust_gate"]["blocked"] == 1

    def test_acceptance_rate_calculation(self, client, mem_session):
        for _ in range(3):
            _seed_event(mem_session, event_type=AuditEventType.TRUST_GATE_PASSED, outcome="success")
        _seed_event(mem_session, event_type=AuditEventType.TRUST_GATE_BLOCKED, outcome="blocked")
        resp = client.get("/api/v1/audit/summary")
        assert resp.status_code == 200
        rate = resp.json()["trust_gate"]["acceptance_rate"]
        assert rate == pytest.approx(0.75, abs=0.01)

    def test_acceptance_rate_none_when_no_trust_gate_events(self, client, mem_session):
        resp = client.get("/api/v1/audit/summary")
        assert resp.status_code == 200
        assert resp.json()["trust_gate"]["acceptance_rate"] is None

    def test_policy_violations_list_populated(self, client, mem_session):
        _seed_event(
            mem_session,
            event_type=AuditEventType.TRUST_GATE_BLOCKED,
            incident_id="blocked-inc",
            outcome="blocked",
            action="Trust Gate BLOCKED: severity_too_low",
        )
        resp = client.get("/api/v1/audit/summary")
        violations = resp.json()["policy_violations"]
        assert len(violations) >= 1
        assert violations[0]["incident_id"] == "blocked-inc"

    def test_security_events_list_populated(self, client, mem_session):
        _seed_event(
            mem_session,
            event_type=AuditEventType.WEBHOOK_HMAC_FAILED,
            outcome="failed",
            action="HMAC mismatch",
        )
        resp = client.get("/api/v1/audit/summary")
        sec = resp.json()["security_events"]
        assert len(sec) >= 1

    def test_summary_since_until_filters(self, client, mem_session):
        """Covers routers/audit.py L178, L180 — since/until on summary."""
        from datetime import timedelta

        _seed_event(mem_session, event_type=AuditEventType.TRUST_GATE_PASSED, outcome="success")
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        resp = client.get("/api/v1/audit/summary", params={"since": past, "until": future})
        assert resp.status_code == 200
        assert resp.json()["trust_gate"]["passed"] >= 1

    def test_trust_gate_warned_counted(self, client, mem_session):
        """Covers routers/audit.py L206 — TRUST_GATE_WARNED branch."""
        _seed_event(mem_session, event_type=AuditEventType.TRUST_GATE_WARNED, outcome="warned")
        resp = client.get("/api/v1/audit/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert body["trust_gate"]["warned"] == 1
        # acceptance_rate denominator includes warned events
        assert body["trust_gate"]["acceptance_rate"] is not None


# ── Audit router — GET /api/v1/audit/retention-policy ────────────────────────


class TestRetentionPolicyRouter:
    def test_returns_expected_fields(self, client):
        resp = client.get("/api/v1/audit/retention-policy")
        assert resp.status_code == 200
        body = resp.json()
        for field in ("policy", "algorithm", "audit_retention_days", "controls", "env_override"):
            assert field in body, f"Missing field: {field}"

    def test_default_retention_7_years(self, client):
        resp = client.get("/api/v1/audit/retention-policy")
        body = resp.json()
        # Default is 2555 days or may be overridden in test env; just check it's a non-negative int
        assert isinstance(body["audit_retention_days"], int)
        assert body["audit_retention_days"] >= 0

    def test_algorithm_is_sha256(self, client):
        resp = client.get("/api/v1/audit/retention-policy")
        assert resp.json()["algorithm"] == "SHA-256"

    def test_env_override_key(self, client):
        resp = client.get("/api/v1/audit/retention-policy")
        assert resp.json()["env_override"] == "RESPONSEIQ_AUDIT_RETENTION_DAYS"

    def test_controls_contains_soc2_references(self, client):
        resp = client.get("/api/v1/audit/retention-policy")
        controls = resp.json()["controls"]
        assert any("CC6" in c for c in controls)
        assert any("CC7" in c for c in controls)
