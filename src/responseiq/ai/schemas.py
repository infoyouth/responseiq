# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Pydantic response-model contracts for structured LLM outputs.

``instructor`` uses these models to enforce schema compliance at the token
sampling level — the LLM cannot return a wrong field type or invalid
severity value. ``IncidentAnalysis`` covers both triage and patch
synthesis; ``ReproductionCode`` wraps the raw pytest repro script.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class IncidentAnalysis(BaseModel):
    """Structured output for incident triage / patch synthesis LLM calls."""

    title: str = Field(description="One-line incident headline (no markdown)")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Severity level — must be exactly one of: low, medium, high, critical"
    )
    description: str = Field(description="Root-cause explanation referencing specific log lines or stack frames")
    remediation: str = Field(
        description=(
            "Precise operational action or code change. Prefer a unified-diff snippet when source code is provided."
        )
    )


class ReproductionCode(BaseModel):
    """Structured output for reproduction test generation."""

    code: str = Field(
        description=(
            "Complete, self-contained pytest script. "
            "Must use standard pytest assertions. "
            "Must FAIL against the buggy code and PASS after the fix. "
            "No markdown fences, only raw Python."
        ),
        min_length=10,
    )
