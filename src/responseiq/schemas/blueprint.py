# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Pydantic models for remediation blueprints.

A ``Blueprint`` describes a known fix pattern with ordered ``Action``
steps and optional ``RollbackStep`` entries. Loaded from YAML/JSON by
``blueprints/loader.py`` and served via the blueprints router.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class Action(BaseModel):
    type: str
    target: Optional[str] = None
    patch: Optional[str] = None


class RollbackStep(BaseModel):
    type: str
    target: Optional[str] = None
    command: Optional[str] = None


class Blueprint(BaseModel):
    id: str
    title: str
    incident_signature: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    rationale: Optional[str] = None
    confidence: Optional[float] = Field(default=0.0)
    blast_radius: Optional[str] = None
    actions: List[Action] = Field(default_factory=list)
    rollback: List[RollbackStep] = Field(default_factory=list)
    examples: List[dict] = Field(default_factory=list)
