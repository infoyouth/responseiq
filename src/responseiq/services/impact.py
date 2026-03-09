# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Incident impact scoring.

Computes a numeric impact score (0–100) from severity level and blast
radius surface area. Used by the Trust Gate to decide whether an
auto-apply or PR-only policy applies to a given incident.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SEVERITY_BASE = {
    "low": 15.0,
    "medium": 35.0,
    "high": 60.0,
    "critical": 80.0,
}

SURFACE_BASE = {
    "single_service": 10.0,
    "multi_service": 20.0,
    "env_wide": 30.0,
}


@dataclass
class ImpactAssessment:
    score: float
    factors: dict[str, Any]


def infer_affected_surface(text: str) -> str:
    content = (text or "").lower()
    if any(token in content for token in ["cluster", "global", "all services", "namespace", "region"]):
        return "env_wide"
    if any(token in content for token in ["upstream", "dependency", "multiple", "cross-service", "gateway"]):
        return "multi_service"
    return "single_service"


def _normalize_confidence(confidence: float | None, source: str | None) -> float:
    if confidence is not None:
        return max(0.0, min(1.0, confidence))

    if (source or "").lower() == "ai":
        return 0.8
    if (source or "").lower() == "rule-engine":
        return 0.65
    return 0.6


def assess_impact(
    *,
    severity: str | None,
    title: str | None = None,
    description: str | None = None,
    source: str | None = None,
    recurrence: int = 1,
    confidence: float | None = None,
    affected_surface: str | None = None,
) -> ImpactAssessment:
    normalized_severity = (severity or "medium").lower()
    severity_base = SEVERITY_BASE.get(normalized_severity, SEVERITY_BASE["medium"])

    resolved_surface = affected_surface or infer_affected_surface(f"{title or ''} {description or ''}")
    surface_base = SURFACE_BASE.get(resolved_surface, SURFACE_BASE["single_service"])

    bounded_recurrence = max(1, recurrence)
    recurrence_points = min((bounded_recurrence - 1) * 5.0, 20.0)

    normalized_confidence = _normalize_confidence(confidence, source)
    confidence_multiplier = 0.7 + (0.3 * normalized_confidence)

    raw_score = (severity_base + surface_base + recurrence_points) * confidence_multiplier
    score = round(max(0.0, min(100.0, raw_score)), 2)

    return ImpactAssessment(
        score=score,
        factors={
            "severity": normalized_severity,
            "affected_surface": resolved_surface,
            "recurrence": bounded_recurrence,
            "confidence": round(normalized_confidence, 2),
            "source": source or "unknown",
        },
    )
