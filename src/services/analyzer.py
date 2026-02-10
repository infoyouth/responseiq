from typing import Optional

# Ensure parsers are registered
import src.parsers  # noqa: F401
from src.ai.llm_service import analyze_with_llm
from src.parsers.registry import registry
from src.schemas.incident import IncidentOut


def analyze_message(message: str) -> Optional[dict]:
    """
    Analyzes a message using AI (if enabled) or falls back to registered parsers.
    Returns a dict with severity and reason/title.
    """
    # 1. AI Analysis Layer (Primary)
    llm_result = analyze_with_llm(message)
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


def analyze_log(log_text: str) -> Optional[IncidentOut]:
    """
    Event-oriented analyzer using Strategy Pattern + AI.
    Delegates to AI first, then parsers.
    """
    # 1. AI
    llm_result = analyze_with_llm(log_text)
    if llm_result:
        return IncidentOut(
            id=None,
            title=llm_result.get("title", "AI Detected Incident"),
            severity=llm_result.get("severity", "medium").lower(),
            description=llm_result.get("description", "No description provided by AI"),
        )

    # 2. Parsers
    parser = registry.find_parser(log_text)
    if parser:
        data = parser.parse(log_text)
        if data:
            return IncidentOut(
                id=None,
                title=data.get("title", "Unknown Incident"),
                severity=data.get("severity", "medium"),
                description=f"Detected {data.get('title')} from logs",
            )
    return None
