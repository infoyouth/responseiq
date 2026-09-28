# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Agent state TypedDict for the remediation state machine.

Carries all mutable fields — retry count, current patch, trace ID,
and investigation report — between the nodes of the remediation graph
without coupling them to any specific service.
"""

from typing import List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    attempt_history: List[str]
    retry_count: int
    incident_id: str
    investigation_report: Optional[str]
    current_patch: Optional[str]
    last_verification: Optional[str]
    status: Optional[str]
    trace_id: Optional[str]
    context: Optional[dict]
