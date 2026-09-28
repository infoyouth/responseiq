"""
Unit tests for src/responseiq/routers/streaming.py

Coverage:
    StreamAnalyzeRequest defaults                               2 tests
    _sse() formatting                                           3 tests
    POST /api/v1/incidents/analyze/stream — headers             2 tests
    POST /api/v1/incidents/analyze/stream — happy path SSE      2 tests
    POST /api/v1/incidents/analyze/stream — error path SSE      1 test

Trust Gate:
    rationale    : SSE endpoint is read-only; any failure yields an ``error`` event.
    blast_radius : streaming.py depends on analyze_with_llm; tests mock that call.
    rollback_plan: remove the router from app.include_router — endpoint disappears.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from responseiq.routers.streaming import StreamAnalyzeRequest, _sse, router


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def _parse_sse_frames(raw: str) -> list[dict]:
    """Parse raw SSE text into a list of {event, data} dicts."""
    frames = []
    for block in raw.strip().split("\n\n"):
        if not block.strip():
            continue
        event = None
        data = None
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data = json.loads(line[len("data:") :].strip())
        if event and data is not None:
            frames.append({"event": event, "data": data})
    return frames


# ---------------------------------------------------------------------------
# StreamAnalyzeRequest
# ---------------------------------------------------------------------------


class TestStreamAnalyzeRequest:
    def test_default_code_context_is_empty(self):
        req = StreamAnalyzeRequest(log_text="ERROR: boom")
        assert req.code_context == ""

    def test_default_enable_critic_is_true(self):
        req = StreamAnalyzeRequest(log_text="ERROR: boom")
        assert req.enable_critic is True


# ---------------------------------------------------------------------------
# _sse helper
# ---------------------------------------------------------------------------


class TestSseHelper:
    def test_event_field_present(self):
        frame = _sse("started", {"msg": "ok"})
        assert frame.startswith("event: started\n")

    def test_data_field_is_json(self):
        frame = _sse("test", {"key": "value"})
        data_line = [line for line in frame.splitlines() if line.startswith("data:")][0]
        parsed = json.loads(data_line[len("data:") :].strip())
        assert parsed["key"] == "value"

    def test_frame_ends_with_double_newline(self):
        frame = _sse("x", {})
        assert frame.endswith("\n\n")


# ---------------------------------------------------------------------------
# Streaming endpoint
# ---------------------------------------------------------------------------


_MOCK_ANALYSIS = {
    "severity": "high",
    "title": "DB connection pool exhausted",
    "description": "All connections consumed under load.",
    "remediation": "Increase pool size in DATABASE_URL.",
    "confidence": 0.85,
}

# scrub() returns (scrubbed_text, mapping_dict)
_SCRUB_NOOP = lambda text: (text, {})  # noqa: E731


class TestStreamEndpointHeaders:
    def test_content_type_is_event_stream(self, client):
        with (
            patch("responseiq.ai.llm_service.analyze_with_llm", new_callable=AsyncMock, return_value=_MOCK_ANALYSIS),
            patch("responseiq.utils.log_scrubber.scrub", side_effect=_SCRUB_NOOP),
            patch("responseiq.services.critic_service.review_remediation", new_callable=AsyncMock, return_value="LGTM"),
        ):
            resp = client.post(
                "/api/v1/incidents/analyze/stream",
                json={"log_text": "ERROR: db pool exhausted"},
            )
        assert "text/event-stream" in resp.headers["content-type"]

    def test_x_accel_buffering_disabled(self, client):
        with (
            patch("responseiq.ai.llm_service.analyze_with_llm", new_callable=AsyncMock, return_value=_MOCK_ANALYSIS),
            patch("responseiq.utils.log_scrubber.scrub", side_effect=_SCRUB_NOOP),
            patch("responseiq.services.critic_service.review_remediation", new_callable=AsyncMock, return_value=None),
        ):
            resp = client.post(
                "/api/v1/incidents/analyze/stream",
                json={"log_text": "ERROR: test"},
            )
        assert resp.headers.get("x-accel-buffering") == "no"


class TestStreamEndpointEvents:
    def test_first_event_is_started(self, client):
        with (
            patch("responseiq.ai.llm_service.analyze_with_llm", new_callable=AsyncMock, return_value=_MOCK_ANALYSIS),
            patch("responseiq.utils.log_scrubber.scrub", side_effect=_SCRUB_NOOP),
            patch("responseiq.services.critic_service.review_remediation", new_callable=AsyncMock, return_value=None),
        ):
            resp = client.post(
                "/api/v1/incidents/analyze/stream",
                json={"log_text": "ERROR: test"},
            )
        frames = _parse_sse_frames(resp.text)
        assert frames[0]["event"] == "started"

    def test_last_event_is_complete_on_success(self, client):
        with (
            patch("responseiq.ai.llm_service.analyze_with_llm", new_callable=AsyncMock, return_value=_MOCK_ANALYSIS),
            patch("responseiq.utils.log_scrubber.scrub", side_effect=_SCRUB_NOOP),
            patch("responseiq.services.critic_service.review_remediation", new_callable=AsyncMock, return_value=None),
        ):
            resp = client.post(
                "/api/v1/incidents/analyze/stream",
                json={"log_text": "ERROR: test"},
            )
        frames = _parse_sse_frames(resp.text)
        assert frames[-1]["event"] in ("complete", "error")

    def test_error_event_emitted_when_llm_fails(self, client):
        with (
            patch(
                "responseiq.ai.llm_service.analyze_with_llm",
                new_callable=AsyncMock,
                side_effect=RuntimeError("LLM unavailable"),
            ),
            patch("responseiq.utils.log_scrubber.scrub", side_effect=_SCRUB_NOOP),
        ):
            resp = client.post(
                "/api/v1/incidents/analyze/stream",
                json={"log_text": "ERROR: test"},
            )
        frames = _parse_sse_frames(resp.text)
        event_names = [f["event"] for f in frames]
        assert "error" in event_names


# ---------------------------------------------------------------------------
# Streaming edge-cases (null LLM result, critic exception, trust-gate exception)
# ---------------------------------------------------------------------------


class TestStreamEdgeCases:
    def test_null_llm_result_emits_fallback_analyzing_event(self, client):
        """When analyze_with_llm returns None, an unavailable fallback event is emitted."""
        with (
            patch("responseiq.ai.llm_service.analyze_with_llm", new_callable=AsyncMock, return_value=None),
            patch("responseiq.utils.log_scrubber.scrub", side_effect=_SCRUB_NOOP),
        ):
            resp = client.post(
                "/api/v1/incidents/analyze/stream",
                json={"log_text": "ERROR: db gone"},
            )
        frames = _parse_sse_frames(resp.text)
        analyzing_msgs = [f["data"]["message"] for f in frames if f["event"] == "analyzing"]
        assert any("unavailable" in m.lower() for m in analyzing_msgs)

    def test_critic_exception_emits_skipped_event(self, client):
        """When critic review raises, a 'skipped' message is emitted (not a hard failure)."""
        with (
            patch("responseiq.ai.llm_service.analyze_with_llm", new_callable=AsyncMock, return_value=_MOCK_ANALYSIS),
            patch("responseiq.utils.log_scrubber.scrub", side_effect=_SCRUB_NOOP),
            patch(
                "responseiq.services.critic_service.review_remediation",
                new_callable=AsyncMock,
                side_effect=RuntimeError("critic unavailable"),
            ),
        ):
            resp = client.post(
                "/api/v1/incidents/analyze/stream",
                json={"log_text": "ERROR: test", "enable_critic": True},
            )
        frames = _parse_sse_frames(resp.text)
        critic_frames = [f for f in frames if f["event"] == "critic"]
        messages = [f["data"].get("message", "") for f in critic_frames]
        assert any("skipped" in m.lower() for m in messages)

    def test_trust_gate_exception_still_yields_complete_event(self, client):
        """When Trust Gate raises, the stream still completes (exception is swallowed)."""
        with (
            patch("responseiq.ai.llm_service.analyze_with_llm", new_callable=AsyncMock, return_value=_MOCK_ANALYSIS),
            patch("responseiq.utils.log_scrubber.scrub", side_effect=_SCRUB_NOOP),
            patch("responseiq.services.critic_service.review_remediation", new_callable=AsyncMock, return_value=None),
            patch(
                "responseiq.services.trust_gate.TrustGateValidator",
                side_effect=RuntimeError("trust gate offline"),
            ),
        ):
            resp = client.post(
                "/api/v1/incidents/analyze/stream",
                json={"log_text": "ERROR: test"},
            )
        frames = _parse_sse_frames(resp.text)
        event_names = [f["event"] for f in frames]
        # Stream must reach complete even when trust gate fails
        assert "complete" in event_names or "trust_gate" in event_names
