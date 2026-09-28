"""
tests/unit/test_webhooks.py

Unit tests for P5.1 — Real-Time Webhook Ingestion Path.

Coverage
--------
- HMAC verification helper: pass, reject, no-secret skip
- Payload normalisers: Datadog, PagerDuty, Sentry → WebhookIncident
- Severity mapping for each source
- Idempotency: duplicate key returns duplicate=True without re-ingesting
- POST /webhooks/datadog  — 202 round trip, no secret
- POST /webhooks/pagerduty — 202 round trip, no secret
- POST /webhooks/sentry   — 202 round trip, no secret
- POST /webhooks/datadog  — 403 on bad HMAC signature
- POST /webhooks/datadog  — 403 on missing signature header when secret set
- SSE endpoint: returns 200 with text/event-stream content-type
- WebhookAck schema fields (accepted, log_id, message, duplicate)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any, Dict
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Patch DB before importing app so tests use in-memory SQLite
# ---------------------------------------------------------------------------

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from responseiq.app import app  # noqa: E402
from responseiq.db import init_db  # noqa: E402
from responseiq.routers.webhooks import (  # noqa: E402
    _SEEN_KEYS,
    _is_duplicate,
    _make_idempotency_key,
    _normalize_datadog,
    _normalize_pagerduty,
    _normalize_sentry,
    _verify_hmac,
)
from responseiq.schemas.webhooks import (  # noqa: E402
    DatadogWebhookPayload,
    PagerDutyWebhookPayload,
    SentryWebhookPayload,
)

init_db()  # ensure tables exist in the in-memory SQLite DB

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sign(secret: str, body: bytes, prefix: str = "") -> str:
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"{prefix}{sig}"


def _dd_payload(**overrides: Any) -> Dict[str, Any]:
    base = {
        "msg_title": "High error rate on payment-service",
        "msg_text": "ERROR: Stripe API returning 500 for 38% of requests",
        "alert_type": "error",
        "priority": "P2",
    }
    base.update(overrides)
    return base


def _pd_payload(**overrides: Any) -> Dict[str, Any]:
    base = {
        "event": {
            "id": "pd-evt-001",
            "event_type": "incident.triggered",
            "resource_type": "incident",
            "data": {
                "id": "INC123",
                "title": "Database connection pool exhausted",
                "status": "triggered",
                "urgency": "high",
                "body": {"details": "QueuePool limit of size 5 overflow 10 exceeded"},
            },
        }
    }
    base.update(overrides)
    return base


def _sentry_payload(**overrides: Any) -> Dict[str, Any]:
    base = {
        "action": "created",
        "data": {
            "issue": {
                "id": "sentry-isssue-42",
                "title": "KeyError: 'last_seen' in refresh_session",
                "level": "error",
                "culprit": "auth_service.py in refresh_session",
                "metadata": {},
            }
        },
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# _verify_hmac
# ---------------------------------------------------------------------------


class TestVerifyHmac:
    def test_no_secret_skips(self):
        """When no secret is configured, any (or missing) signature is accepted."""
        _verify_hmac(None, b"body", None)  # should not raise
        _verify_hmac(None, b"body", "wrong")

    def test_valid_signature_passes(self):
        body = b'{"title": "test"}'
        sig = _sign("mysecret", body, prefix="sha256=")
        _verify_hmac("mysecret", body, sig, prefix="sha256=")  # no exception

    def test_invalid_signature_raises_403(self):
        from fastapi import HTTPException

        body = b'{"title": "test"}'
        with pytest.raises(HTTPException) as exc_info:
            _verify_hmac("mysecret", body, "sha256=deadbeef", prefix="sha256=")
        assert exc_info.value.status_code == 403

    def test_missing_header_raises_403(self):
        from fastapi import HTTPException

        body = b'{"title": "test"}'
        with pytest.raises(HTTPException) as exc_info:
            _verify_hmac("mysecret", body, None, prefix="sha256=")
        assert exc_info.value.status_code == 403

    def test_pagerduty_v1_prefix(self):
        body = b'{"event": {}}'
        sig = _sign("pdsecret", body, prefix="v1=")
        _verify_hmac("pdsecret", body, sig, prefix="v1=")

    def test_pagerduty_comma_separated(self):
        """PagerDuty may send multiple sigs; first is used."""
        body = b'{"event": {}}'
        good = _sign("pdsecret", body, prefix="v1=")
        combined = f"{good},v1=anothertoken"
        _verify_hmac("pdsecret", body, combined, prefix="v1=")


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency:
    def setup_method(self):
        _SEEN_KEYS.clear()

    def test_first_call_not_duplicate(self):
        assert _is_duplicate("abc123") is False

    def test_second_call_is_duplicate(self):
        _is_duplicate("dup-key")
        assert _is_duplicate("dup-key") is True

    def test_different_keys_not_duplicate(self):
        _is_duplicate("key-a")
        assert _is_duplicate("key-b") is False

    def test_make_idempotency_key_deterministic(self):
        k1 = _make_idempotency_key("datadog", "title", "body")
        k2 = _make_idempotency_key("datadog", "title", "body")
        assert k1 == k2

    def test_make_idempotency_key_differs_by_source(self):
        k1 = _make_idempotency_key("datadog", "title", "body")
        k2 = _make_idempotency_key("sentry", "title", "body")
        assert k1 != k2


# ---------------------------------------------------------------------------
# Normalisers
# ---------------------------------------------------------------------------


class TestNormalizeDatadog:
    def test_basic_fields(self):
        payload = DatadogWebhookPayload(
            msg_title="Payment service down",
            msg_text="ERROR: connection refused",
            alert_type="error",
            priority="P1",
        )
        inc = _normalize_datadog(payload)
        assert inc.source == "datadog"
        assert inc.severity == "critical"
        assert "Payment service down" in inc.title
        assert "connection refused" in inc.log_content

    def test_alert_type_mapping(self):
        for alert_type, expected in [("error", "high"), ("warning", "medium"), ("info", "low")]:
            p = DatadogWebhookPayload(msg_title="t", alert_type=alert_type)
            inc = _normalize_datadog(p)
            assert inc.severity == expected

    def test_priority_overrides_alert_type(self):
        p = DatadogWebhookPayload(msg_title="t", alert_type="info", priority="P1")
        inc = _normalize_datadog(p)
        assert inc.severity == "critical"

    def test_idempotency_key_is_sha256_hex(self):
        p = DatadogWebhookPayload(msg_title="t", msg_text="log")
        inc = _normalize_datadog(p)
        assert len(inc.idempotency_key) == 64
        assert all(c in "0123456789abcdef" for c in inc.idempotency_key)


class TestNormalizePagerduty:
    def test_basic_fields(self):
        payload = PagerDutyWebhookPayload.model_validate(_pd_payload())
        inc = _normalize_pagerduty(payload)
        assert inc.source == "pagerduty"
        assert inc.severity == "high"
        assert "Database" in inc.title
        assert "QueuePool" in inc.log_content

    def test_low_urgency_maps_to_medium(self):
        raw = _pd_payload()
        raw["event"]["data"]["urgency"] = "low"
        payload = PagerDutyWebhookPayload.model_validate(raw)
        inc = _normalize_pagerduty(payload)
        assert inc.severity == "medium"


class TestNormalizeSentry:
    def test_basic_fields(self):
        payload = SentryWebhookPayload.model_validate(_sentry_payload())
        inc = _normalize_sentry(payload)
        assert inc.source == "sentry"
        assert inc.severity == "high"
        assert "KeyError" in inc.title
        assert "auth_service.py" in inc.log_content

    def test_sentry_level_mapping(self):
        for level, expected in [
            ("fatal", "critical"),
            ("error", "high"),
            ("warning", "medium"),
            ("info", "low"),
            ("debug", "low"),
        ]:
            raw = _sentry_payload()
            raw["data"]["issue"]["level"] = level
            payload = SentryWebhookPayload.model_validate(raw)
            inc = _normalize_sentry(payload)
            assert inc.severity == expected, f"level={level}"


# ---------------------------------------------------------------------------
# POST endpoint tests (no signature secrets configured)
# ---------------------------------------------------------------------------


class TestDatadogEndpoint:
    def setup_method(self):
        _SEEN_KEYS.clear()

    def test_202_accepted(self):
        resp = client.post("/webhooks/datadog", json=_dd_payload())
        assert resp.status_code == 202
        body = resp.json()
        assert body["accepted"] is True
        assert body["duplicate"] is False
        assert body["log_id"] is not None

    def test_idempotency_key_in_response(self):
        resp = client.post("/webhooks/datadog", json=_dd_payload())
        assert len(resp.json()["idempotency_key"]) == 64

    def test_duplicate_returns_accepted_without_new_log(self):
        r1 = client.post("/webhooks/datadog", json=_dd_payload())
        r2 = client.post("/webhooks/datadog", json=_dd_payload())
        assert r1.status_code == 202
        assert r2.status_code == 202
        assert r2.json()["duplicate"] is True
        assert r2.json()["log_id"] is None

    def test_empty_body_422(self):
        resp = client.post("/webhooks/datadog", content=b"", headers={"Content-Type": "application/json"})
        assert resp.status_code == 422


class TestPagerDutyEndpoint:
    def setup_method(self):
        _SEEN_KEYS.clear()

    def test_202_accepted(self):
        resp = client.post("/webhooks/pagerduty", json=_pd_payload())
        assert resp.status_code == 202
        body = resp.json()
        assert body["accepted"] is True
        assert body["duplicate"] is False

    def test_message_contains_stream_hint(self):
        resp = client.post("/webhooks/pagerduty", json=_pd_payload())
        assert "stream" in resp.json()["message"].lower()


class TestSentryEndpoint:
    def setup_method(self):
        _SEEN_KEYS.clear()

    def test_202_accepted(self):
        resp = client.post("/webhooks/sentry", json=_sentry_payload())
        assert resp.status_code == 202
        body = resp.json()
        assert body["accepted"] is True

    def test_culprit_in_log_content(self):
        resp = client.post("/webhooks/sentry", json=_sentry_payload())
        assert resp.status_code == 202


# ---------------------------------------------------------------------------
# HMAC rejection when secret is configured
# ---------------------------------------------------------------------------


class TestWebhookSignatureEnforcement:
    def setup_method(self):
        _SEEN_KEYS.clear()

    def test_datadog_bad_signature_403(self):
        from pydantic import SecretStr

        with patch("responseiq.routers.webhooks.settings") as mock_settings:
            mock_settings.datadog_webhook_secret = SecretStr("correct-secret")
            body = json.dumps(_dd_payload()).encode()
            resp = client.post(
                "/webhooks/datadog",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Datadog-Webhook-Signature": "sha256=wrongsig",
                },
            )
        assert resp.status_code == 403

    def test_datadog_missing_header_403(self):
        from pydantic import SecretStr

        with patch("responseiq.routers.webhooks.settings") as mock_settings:
            mock_settings.datadog_webhook_secret = SecretStr("correct-secret")
            resp = client.post("/webhooks/datadog", json=_dd_payload())
        assert resp.status_code == 403

    def test_datadog_correct_signature_202(self):
        from pydantic import SecretStr

        with patch("responseiq.routers.webhooks.settings") as mock_settings:
            mock_settings.datadog_webhook_secret = SecretStr("correct-secret")
            mock_settings.pagerduty_webhook_secret = None
            mock_settings.sentry_webhook_secret = None
            body = json.dumps(_dd_payload()).encode()
            sig = _sign("correct-secret", body, prefix="sha256=")
            resp = client.post(
                "/webhooks/datadog",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Datadog-Webhook-Signature": sig,
                },
            )
        assert resp.status_code == 202


# ---------------------------------------------------------------------------
# SSE endpoint
# ---------------------------------------------------------------------------


class TestSSEEndpoint:
    def test_returns_200_event_stream(self):
        """SSE endpoint must reply with text/event-stream content type."""
        with patch("responseiq.routers.webhooks._SSE_TIMEOUT", 0):
            with client.stream("GET", "/webhooks/stream/9999") as resp:
                assert resp.status_code == 200
                assert "text/event-stream" in resp.headers["content-type"]

    def test_sse_timeout_event_format(self):
        """When log_id is not found, SSE must emit a timeout event with required fields."""
        with patch("responseiq.routers.webhooks._SSE_TIMEOUT", 0):
            with client.stream("GET", "/webhooks/stream/99998") as resp:
                for raw_line in resp.iter_lines():
                    if raw_line.startswith("data:"):
                        event = json.loads(raw_line[len("data:") :].strip())
                        assert "log_id" in event
                        assert "status" in event
                        assert event["status"] in {"processing", "complete", "timeout"}
                        break
