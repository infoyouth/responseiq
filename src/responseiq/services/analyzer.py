# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Log message analyzer entry point.

Routes each incoming log message through the registered parser chain
and then to the LLM service for triage. Returns a structured
``IncidentOut`` with severity, title, and remediation suggestion.
"""

from typing import Optional

# Ensure parsers are registered
import responseiq.parsers  # noqa: F401
from responseiq.ai.llm_service import analyze_with_llm
from responseiq.parsers.registry import registry
from responseiq.schemas.incident import IncidentOut


def analyze_message(message: str) -> Optional[dict]:
    """
    Wrapper for sync calls if needed, but preferable to use async version.
    DEPRECATED: Use analyze_message_async instead.
    """
    import asyncio

    return asyncio.run(analyze_message_async(message))


async def analyze_message_async(message: str) -> Optional[dict]:
    """
    Analyzes a message using AI (if enabled) or falls back to registered parsers.
    Returns a dict with severity and reason/title.
    """
    # 0. Context Extraction
    from responseiq.utils.context_extractor import extract_context_from_log

    code_context = await extract_context_from_log(message)

    # 1. AI Analysis Layer (Primary)
    llm_result = await analyze_with_llm(message, code_context=code_context)
    if llm_result:
        return {
            "severity": llm_result.get("severity", "medium").lower(),
            "reason": f"AI: {llm_result.get('title', 'Detected Issue')}",
            "description": llm_result.get("description"),
            "remediation": llm_result.get("remediation"),
            "source": "ai",
        }

    # 2. Heuristic/Parser Layer (Fallback)
    parser = registry.find_parser(message)
    if parser:
        result = parser.parse(message)
        if result:
            return {
                "severity": result.get("severity", "medium"),
                "reason": f"matched:{result.get('title', 'keyword')}",
                "source": "rule-engine",
            }
    return None


async def analyze_log_async(log_text: str) -> Optional[IncidentOut]:
    """
    Event-oriented analyzer using Strategy Pattern + AI.
    Annotated Async version.
    """
    # 0. Context Extraction (Magical Step)
    # We try to find the source code related to the log
    from responseiq.utils.context_extractor import extract_context_from_log

    code_context = await extract_context_from_log(log_text)

    # 1. AI
    llm_result = await analyze_with_llm(log_text, code_context=code_context)
    if llm_result:
        return IncidentOut(
            id=None,
            title=llm_result.get("title", "AI Detected Incident"),
            severity=llm_result.get("severity", "medium").lower(),
            description=llm_result.get("description"),
            source="ai",
        )

    # 2. Parsers
    parser = registry.find_parser(log_text)
    if parser:
        data = parser.parse(log_text)
        if data:
            return IncidentOut(
                id=None,
                title=f"Rule: {data.get('title')}",
                severity=data.get("severity", "medium"),
                description=data.get("description", "Matched purely by keyword rules"),
                source="rule-engine",
            )
    return None


def analyze_log(log_text: str) -> Optional[IncidentOut]:
    """
    Synchronous wrapper for analyze_log_async.
    Maintains compatibility with existing synchronous tests and consumers.
    """
    import asyncio

    return asyncio.run(analyze_log_async(log_text))
