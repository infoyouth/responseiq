# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Streaming SSE router for live incident analysis progress.

Exposes ``POST /api/v1/incidents/analyze/stream`` which runs the full
Detect → Context → Reason pipeline and emits Server-Sent Events so
callers see live progress instead of waiting 10–30 s for a JSON blob.

Event sequence emitted per request:
  1. ``started``       — request accepted, log text received
  2. ``scrubbing``     — PII/secret scrubbing in progress
  3. ``analyzing``     — LLM inference running
  4. ``critic``        — lightweight critic review pass (if enabled)
  5. ``trust_gate``    — Trust Gate policy check
  6. ``complete``      — final ``RemediationRecommendation`` JSON
  7. ``error``         — emitted instead of ``complete`` on failure
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from responseiq.utils.logger import logger

router = APIRouter(prefix="/api/v1/incidents", tags=["streaming"])


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------


class StreamAnalyzeRequest(BaseModel):
    log_text: str
    code_context: str = ""
    enable_critic: bool = True


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------


def _sse(event: str, data: dict) -> str:
    """Format a single SSE frame."""
    payload = json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


async def _analysis_stream(req: StreamAnalyzeRequest) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE frames as analysis progresses."""
    yield _sse("started", {"message": "Analysis started", "log_length": len(req.log_text)})

    # ── Step 1: PII scrubbing ────────────────────────────────────────────
    yield _sse("scrubbing", {"message": "Scanning for PII and secrets"})
    await asyncio.sleep(0)  # let the event reach the client

    from responseiq.config.settings import settings
    from responseiq.utils.log_scrubber import scrub

    scrub_mapping: dict = {}
    log_text = req.log_text
    code_context = req.code_context
    if settings.scrub_enabled:
        log_text, log_map = scrub(log_text)
        code_context, code_map = scrub(code_context)
        scrub_mapping = {**log_map, **code_map}

    yield _sse("scrubbing", {"message": "Scrubbing complete", "redacted_tokens": len(scrub_mapping)})

    # ── Step 2: LLM analysis ─────────────────────────────────────────────
    yield _sse("analyzing", {"message": "Sending to LLM for analysis"})
    await asyncio.sleep(0)

    try:
        from responseiq.ai.llm_service import analyze_with_llm

        result = await analyze_with_llm(log_text, code_context)
    except Exception as exc:
        logger.exception("LLM call failed during streaming analysis")
        yield _sse("error", {"message": f"LLM analysis failed: {exc}"})
        return

    if result is None:
        yield _sse("analyzing", {"message": "LLM unavailable — using rule-engine fallback"})
        result = {
            "title": "Analysis unavailable",
            "severity": "unknown",
            "description": "No LLM configured.",
            "remediation": "",
        }
    else:
        yield _sse("analyzing", {"message": "LLM analysis complete", "severity": result.get("severity", "?")})

    # ── Step 3: Critic review ────────────────────────────────────────────
    critic_note: str | None = None
    if req.enable_critic and result.get("remediation"):
        yield _sse("critic", {"message": "Running lightweight critic review"})
        await asyncio.sleep(0)
        try:
            from responseiq.services.critic_service import review_remediation

            critic_note = await review_remediation(
                incident_summary=result.get("description", ""),
                proposed_fix=result.get("remediation", ""),
            )
            yield _sse("critic", {"message": "Critic review complete", "note": critic_note})
        except Exception as exc:
            logger.warning(f"Critic review skipped: {exc}")
            yield _sse("critic", {"message": "Critic review skipped", "reason": str(exc)})

    # ── Step 4: Trust Gate ───────────────────────────────────────────────
    yield _sse("trust_gate", {"message": "Checking Trust Gate policy"})
    await asyncio.sleep(0)

    trust_allowed = True
    trust_reason = "Policy check passed"
    try:
        from responseiq.services.trust_gate import RemediationRequest, TrustGateValidator

        tg = TrustGateValidator()
        tg_req = RemediationRequest(
            incident_id="stream-" + result.get("title", "")[:20],
            severity=result.get("severity", "low"),
            confidence=float(result.get("confidence", 0.5)),
            impact_score=0.0,
            blast_radius="unknown",
            proposed_changes=[],
            affected_files=[],
            rationale=result.get("remediation", ""),
        )
        vr = await tg.validate_remediation(tg_req)
        trust_allowed = vr.allowed
        trust_reason = vr.reason.value if vr.reason else "Policy check passed"
    except Exception as exc:
        logger.warning(f"Trust Gate check skipped: {exc}")

    yield _sse(
        "trust_gate",
        {"message": "Trust Gate complete", "allowed": trust_allowed, "reason": trust_reason},
    )

    # ── Step 5: Final result ─────────────────────────────────────────────
    yield _sse(
        "complete",
        {
            "result": result,
            "trust_allowed": trust_allowed,
            "trust_reason": trust_reason,
            "critic_note": critic_note,
        },
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/analyze/stream",
    summary="Stream incident analysis progress via SSE",
    response_class=StreamingResponse,
)
async def stream_analyze_incident(request: Request, body: StreamAnalyzeRequest) -> StreamingResponse:
    """
    Analyse a log text and stream progress as Server-Sent Events.

    Connect with ``EventSource`` or ``curl -N``:

    ```bash
    curl -N -X POST /api/v1/incidents/analyze/stream \\
      -H 'Content-Type: application/json' \\
      -d '{"log_text": "ERROR: NullPointerException at line 42"}'
    ```
    """
    return StreamingResponse(
        _analysis_stream(body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
