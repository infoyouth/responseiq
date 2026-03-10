# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Multi-agent Critic pattern — lightweight async reviewer LLM pass.

After the Trust Gate approves a proposed fix, this service runs a
second, lightweight LLM pass using the fast model (``gpt-4o-mini`` by
default) to surface logical errors, hidden regressions, and missing
edge cases before the fix is shown to the human.

The critic is **non-blocking**: it runs as a background coroutine and
its output is advisory only — it never blocks or rejects a fix. If the
critic call fails or times out, the original fix is returned unchanged.

Usage:
    ```python
    from responseiq.services.critic_service import review_remediation

    note = await review_remediation(
        incident_summary="NullPointerException in PaymentService.charge()",
        proposed_fix="Add null check before calling .charge()",
    )
    # note is a one-paragraph plain-English critique or None
    ```
"""

from __future__ import annotations

import asyncio
from typing import Optional

from responseiq.ai.model_utils import router as _router
from responseiq.config.settings import settings
from responseiq.utils.logger import logger
from responseiq.utils.tracing import get_langfuse

_CRITIC_SYSTEM_PROMPT = (
    "You are a senior software engineer performing a rapid code review. "
    "You will be given an incident summary and a proposed fix. "
    "Your job is to identify any logical errors, missing edge cases, "
    "hidden regressions, or security concerns in the proposed fix — "
    "in 2–4 sentences of plain English. "
    "If the fix looks correct, say so briefly. Be direct and specific.\n\n"
    "Format: Start with LGTM, WARNING, or CONCERN depending on confidence level."
)

_CRITIC_USER_TEMPLATE = (
    "INCIDENT SUMMARY:\n{incident_summary}\n\nPROPOSED FIX:\n{proposed_fix}\n\nBriefly critique this fix."
)

_CRITIC_TIMEOUT_SECS = 15


async def review_remediation(
    incident_summary: str,
    proposed_fix: str,
) -> Optional[str]:
    """
    Run a lightweight critic review of a proposed fix.

    Returns a one-paragraph plain-English critique, or ``None`` if the
    LLM is unavailable or the review times out.  Never raises.
    """
    if not settings.openai_api_key and not settings.llm_base_url:
        logger.debug("Critic review skipped — no LLM configured")
        return None

    try:
        return await asyncio.wait_for(
            _call_critic_llm(incident_summary, proposed_fix),
            timeout=_CRITIC_TIMEOUT_SECS,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Critic review timed out after {_CRITIC_TIMEOUT_SECS}s — skipping")
        return None
    except Exception as exc:
        logger.warning(f"Critic review failed: {exc} — skipping")
        return None


async def _call_critic_llm(incident_summary: str, proposed_fix: str) -> Optional[str]:
    """Internal: call the fast model and return the raw critique text."""
    import instructor  # type: ignore[import-untyped]
    from openai import AsyncOpenAI

    from responseiq.ai.llm_service import _provider_name
    from opentelemetry import trace as _otel_trace

    tracer = _otel_trace.get_tracer("responseiq.services.critic_service")
    fast_model = _router.model_for("classify_severity")  # fast/cheap route
    prompt = _CRITIC_USER_TEMPLATE.format(
        incident_summary=incident_summary[:1000],
        proposed_fix=proposed_fix[:1000],
    )

    # Langfuse trace (no-op when not configured)
    lf = get_langfuse()
    lf_gen = None
    if lf:
        lf_gen = lf.start_generation(
            name="critic_review",
            model=fast_model,
            input=prompt,
        )

    api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else "ollama"

    with tracer.start_as_current_span("gen_ai.critic_review") as span:
        span.set_attribute("gen_ai.system", _provider_name())
        span.set_attribute("gen_ai.request.model", fast_model)
        span.set_attribute("gen_ai.operation.name", "chat")

        if settings.llm_base_url:
            raw_client = AsyncOpenAI(api_key=api_key, base_url=settings.llm_base_url)
            client = instructor.from_openai(raw_client, mode=instructor.Mode.JSON)
        else:
            client = instructor.from_openai(AsyncOpenAI(api_key=api_key))

        # Use raw text response via a simple Pydantic wrapper
        from pydantic import BaseModel

        class CritiqueResponse(BaseModel):
            critique: str

        resp: CritiqueResponse = await client.chat.completions.create(
            model=fast_model,
            response_model=CritiqueResponse,
            messages=[
                {"role": "system", "content": _CRITIC_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=256,
        )
        span.set_attribute("gen_ai.response.model", fast_model)

    if lf_gen:
        lf_gen.update(output=resp.critique[:200])
        lf_gen.end()

    logger.debug(f"Critic review: {resp.critique[:100]}")
    return resp.critique
