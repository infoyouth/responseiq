# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Schemas for the causal root-cause graph (P6).

Represents a machine-readable causal chain from deploy event through
latency spike to the specific crashing code line. Plain JSON output
so SRE dashboards and post-incident tools can ingest it directly.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    DEPLOY_EVENT = "deploy_event"
    LATENCY_SPIKE = "latency_spike"
    ERROR_LOG = "error_log"
    AFFECTED_CODE = "affected_code"
    POLICY_DECISION = "policy_decision"
    UNKNOWN = "unknown"


class EdgeType(str, Enum):
    CAUSED = "caused"
    CORRELATED = "correlated"
    TRIGGERED = "triggered"
    BLOCKED = "blocked"


class CausalNode(BaseModel):
    """A single node in the causal graph."""

    id: str = Field(description="Unique node identifier within the graph")
    type: NodeType
    label: str = Field(description="Human-readable one-line description")
    detail: Optional[str] = Field(default=None, description="Extended detail or raw value")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CausalEdge(BaseModel):
    """A directed edge between two causal nodes."""

    source_id: str
    target_id: str
    type: EdgeType = EdgeType.CAUSED
    label: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class CausalGraph(BaseModel):
    """
    Complete causal graph for a single incident remediation run.

    Fields
    ------
    incident_id   : The incident being analysed.
    nodes         : Ordered list of causal nodes (root → leaf).
    edges         : Directed edges encoding causal / correlation links.
    summary       : Human-readable one-paragraph narrative of the causal chain.
    confidence    : Overall graph confidence (min of all edge confidences).
    """

    incident_id: str
    nodes: List[CausalNode] = Field(default_factory=list)
    edges: List[CausalEdge] = Field(default_factory=list)
    summary: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
