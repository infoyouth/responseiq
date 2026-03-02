"""
src/responseiq/ai/schemas.py

Pydantic response-model contracts for structured LLM outputs.

These models are used by ``instructor`` to enforce schema compliance at the
token-sampling level — the LLM is mathematically incapable of returning a
field with the wrong type or an invalid severity value.

Design notes
------------
* ``IncidentAnalysis`` — used for both incident triage and patch synthesis.
  Maps 1-to-1 with the dict contract the rest of the codebase already expects,
  so downstream code requires zero changes.
* ``ReproductionCode`` — wraps the raw Python string returned by the repro
  endpoint so instructor can validate it is non-empty.
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
