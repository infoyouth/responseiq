# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""LLM analysis and reproduction-code generation.

Wraps the OpenAI async client with ``instructor`` for Pydantic-enforced
structured outputs, so the LLM is constrained to return a valid
``IncidentAnalysis`` or ``ReproductionCode`` object every time. Langfuse
tracing is wired in when keys are present and silently skipped otherwise.

Example:
    ```python
    from responseiq.ai.llm_service import analyze_with_llm

    result = await analyze_with_llm(log_text)
    print(result.severity)  # "high"
    ```
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import instructor  # type: ignore[import-untyped]
from openai import AsyncOpenAI

from responseiq.ai.model_utils import router as _router
from responseiq.ai.schemas import IncidentAnalysis, ReproductionCode
from responseiq.config.settings import settings
from responseiq.utils.log_scrubber import restore, scrub
from responseiq.utils.logger import logger
from responseiq.utils.tracing import get_langfuse

# ---------------------------------------------------------------------------
# System prompts (constants so they can be swapped / optimised with DSPy later)
# ---------------------------------------------------------------------------

_ANALYSIS_SYSTEM_PROMPT = (
    "You are a senior DevOps / SRE Incident Analyzer. "
    "Analyze the log AND the provided source code context. "
    "Pinpoint the exact function and line of code causing the issue when visible. "
    "Return a structured JSON object with keys: title, severity, description, remediation."
)

_REPRO_SYSTEM_PROMPT = "You are a Python focused QA Automation Expert."

_REPRO_USER_TEMPLATE = (
    "You are an expert QA Automation Engineer. "
    "Your goal is to write a standalone Python script using `pytest` that REPRODUCES the bug "
    "described below. The test MUST FAIL against the buggy code and PASS only after the fix.\n\n"
    "INCIDENT SUMMARY:\n{incident_summary}\n\n"
    "RELEVANT SOURCE CODE:\n{relevant_code}\n\n"
    "INSTRUCTIONS:\n"
    "1. Return ONLY the python code inside the `code` field. No markdown, no explanations.\n"
    "2. Use standard `pytest` syntax.\n"
    "3. Assert the specific error condition found in the incident summary.\n"
    "4. Mock external dependencies (network, db, filesystem) where appropriate.\n"
    "5. The test should be self-contained and ready to run."
)

# ---------------------------------------------------------------------------
# Client factory — single injection point for all tests
# ---------------------------------------------------------------------------


def _get_instructor_client() -> instructor.AsyncInstructor:
    """
    Create and return an instructor-wrapped AsyncOpenAI client.

    Supports three backends controlled by env vars:

    1. OpenAI (default):
       Set RESPONSEIQ_OPENAI_API_KEY.

    2. Ollama (free, local):
       RESPONSEIQ_LLM_BASE_URL=http://localhost:11434/v1
       RESPONSEIQ_LLM_ANALYSIS_MODEL=llama3.2  (or any model pulled via `ollama pull`)
       No API key required.

    3. Groq (free cloud tier, fast):
       RESPONSEIQ_LLM_BASE_URL=https://api.groq.com/openai/v1
       RESPONSEIQ_OPENAI_API_KEY=gsk_...  (your Groq key)
       RESPONSEIQ_LLM_ANALYSIS_MODEL=llama-3.1-70b-versatile

    Extracted as a standalone function so unit tests can patch it:
        patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock)
    """
    api_key = (
        settings.openai_api_key.get_secret_value()
        if settings.openai_api_key
        else "ollama"  # Ollama/local endpoints ignore the key; a non-empty string is required by the SDK
    )

    if settings.llm_base_url:
        # OpenAI-compatible endpoint (Ollama, Groq, LM Studio, vLLM, …)
        # instructor.Mode.JSON avoids function-calling which many local models don't support
        client = AsyncOpenAI(api_key=api_key, base_url=settings.llm_base_url)
        return instructor.from_openai(client, mode=instructor.Mode.JSON)

    # Standard OpenAI
    return instructor.from_openai(AsyncOpenAI(api_key=api_key))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def analyze_with_llm(log_text: str, code_context: str = "") -> Optional[Dict[str, Any]]:
    """
    Analyse log using OpenAI (instructor-enforced schema) or fall back to local mock LLM.

    PII scrubbing is applied before any external call when settings.scrub_enabled is True.
    """
    # --- P2.3: PII / secret scrubbing before any external call ---
    scrub_mapping: Dict[str, str] = {}
    if settings.scrub_enabled:
        log_text, log_mapping = scrub(log_text)
        code_context, code_mapping = scrub(code_context)
        scrub_mapping = {**log_mapping, **code_mapping}
        if scrub_mapping:
            logger.info(
                "PII scrubber redacted tokens before LLM call",
                redacted_count=len(scrub_mapping),
            )

    # Try LLM if a key OR a custom base_url (Ollama/Groq/…) is configured
    if settings.openai_api_key or settings.llm_base_url:
        result = await _analyze_with_openai(log_text, code_context)
        if result is not None:
            # Restore placeholders in display fields so local UI shows real values
            if scrub_mapping:
                for field in ("title", "description", "remediation"):
                    if field in result and isinstance(result[field], str):
                        result[field] = restore(result[field], scrub_mapping)
            return result
        logger.warning("OpenAI analysis failed, falling back to local mock LLM")

    # Fall back to local mock LLM
    if settings.use_local_llm_fallback:
        logger.info("Using local mock LLM for incident analysis")
        from responseiq.ai.local_llm_service import analyze_with_local_llm

        return await analyze_with_local_llm(log_text, code_context)

    logger.debug("AI analysis disabled - no OpenAI key and local fallback disabled")
    return None


async def _analyze_with_openai(log_text: str, code_context: str = "") -> Optional[Dict[str, Any]]:
    """
    Instructor-backed OpenAI call that returns a validated ``IncidentAnalysis`` dict.

    instructor enforces the Pydantic schema at the token level — no ``json.loads``,
    no silent parse failures, no unvalidated severity literals.
    """
    if not settings.openai_api_key and not settings.llm_base_url:
        return None

    final_user_content = f"Log content: {log_text}"
    if code_context:
        final_user_content += f"\n\n{code_context}"
        logger.info("Enriched AI Prompt with Source Code Context")

    # Langfuse generation span (no-op when not configured)
    lf = get_langfuse()
    lf_generation = None
    _analysis_model = _router.model_for("analyze")
    if lf:
        lf_generation = lf.start_generation(
            name="analyze_incident",
            model=_analysis_model,
            input=[
                {"role": "system", "content": _ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": final_user_content},
            ],
        )

    try:
        client = _get_instructor_client()
        result: IncidentAnalysis = await client.chat.completions.create(
            model=_analysis_model,
            response_model=IncidentAnalysis,
            messages=[
                {"role": "system", "content": _ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": final_user_content},
            ],
            temperature=0.0,
            max_tokens=settings.llm_max_tokens,
        )

        if lf_generation:
            lf_generation.update(output=result.model_dump())
            lf_generation.end()

        result_dict = result.model_dump()
        result_dict["llm_model_used"] = _analysis_model
        return result_dict

    except Exception as e:
        if lf_generation:
            lf_generation.update(level="ERROR", status_message=str(e))
            lf_generation.end()
        logger.warning(f"LLM analysis failed: {e}. Falling back to local parsers.")
        return None


async def generate_reproduction_code(incident_summary: str, relevant_code: str) -> Optional[str]:
    """
    Ask the LLM to generate a standalone pytest script that reproduces the incident.

    Returns the validated Python code string (via ``ReproductionCode.code``) or None.
    """
    if not settings.openai_api_key and not settings.llm_base_url:
        logger.warning(
            "No LLM configured. Set RESPONSEIQ_OPENAI_API_KEY or RESPONSEIQ_LLM_BASE_URL. Cannot generate reproduction code."
        )
        return None

    # P2.3: scrub before sending to LLM
    scrub_mapping: Dict[str, str] = {}
    if settings.scrub_enabled:
        incident_summary, s_map = scrub(incident_summary)
        relevant_code, c_map = scrub(relevant_code)
        scrub_mapping = {**s_map, **c_map}
        if scrub_mapping:
            logger.info(
                "PII scrubber redacted tokens before reproduction code generation",
                redacted_count=len(scrub_mapping),
            )

    prompt = _REPRO_USER_TEMPLATE.format(
        incident_summary=incident_summary,
        relevant_code=relevant_code,
    )

    # Langfuse generation span
    lf = get_langfuse()
    lf_generation = None
    _repro_model = _router.model_for("generate_repro")
    if lf:
        lf_generation = lf.start_generation(
            name="generate_reproduction_code",
            model=_repro_model,
            input=prompt,
        )

    try:
        client = _get_instructor_client()
        result: ReproductionCode = await client.chat.completions.create(
            model=_repro_model,
            response_model=ReproductionCode,
            messages=[
                {"role": "system", "content": _REPRO_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=settings.llm_repro_max_tokens,
        )

        if lf_generation:
            lf_generation.update(output=result.code[:200])
            lf_generation.end()

        return result.code

    except Exception as e:
        if lf_generation:
            lf_generation.update(level="ERROR", status_message=str(e))
            lf_generation.end()
        logger.exception(f"Error generating reproduction code: {e}")
        return None
