# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Durable Temporal workflow for end-to-end incident remediation.

Implements the state machine: Detect → Context → Notify → Human Approval
→ Learn. Entirely inert until ``TEMPORAL_ENABLED=true`` and a Temporal
server is reachable. Human approval is delivered via the
``receive_approval`` signal, triggered by ``POST /api/v1/feedback``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional

# Guard: only import temporalio decorators when the package is installed
try:
    from temporalio import workflow  # type: ignore[import-untyped]
    from temporalio.common import RetryPolicy  # type: ignore[import-untyped]

    _HAS_TEMPORAL = True
    _workflow_defn = workflow.defn
    _workflow_run = workflow.run
    _workflow_signal = workflow.signal
    _workflow_query = workflow.query
except ImportError:
    _HAS_TEMPORAL = False

    def _workflow_defn(cls):  # type: ignore[misc]
        return cls

    def _workflow_run(func):  # type: ignore[misc]
        return func

    def _workflow_signal(func):  # type: ignore[misc]
        return func

    def _workflow_query(func):  # type: ignore[misc]
        return func


# ── Input / Output dataclasses (no Temporal dependency) ───────────────────────


@dataclass
class RemediationInput:
    """Input for the RemediationWorkflow."""

    log_id: int
    require_approval: bool = True
    approval_timeout_hours: int = 48
    notify_on_start: bool = True


@dataclass
class RemediationResult:
    """Outcome of the RemediationWorkflow run."""

    log_id: int
    analyzed: bool = False
    embedding_stored: bool = False
    approval_required: bool = False
    approved: Optional[bool] = None
    timed_out: bool = False
    error: Optional[str] = None
    workflow_steps: list = field(default_factory=list)


# ── Workflow definition ────────────────────────────────────────────────────────


@_workflow_defn
class RemediationWorkflow:
    """
    Durable remediation workflow.

    Orchestrates: Detect → Context → [Human Gate] → Learn

    This class MUST remain deterministic — no I/O, logging, or imports.
    All external calls are delegated to activities.
    """

    def __init__(self) -> None:
        self._approval_received: bool = False
        self._approval_value: bool = False
        self._approval_comment: str = ""

    # ── Signals ───────────────────────────────────────────────────────────────

    @_workflow_signal
    async def receive_approval(self, approved: bool, comment: str = "") -> None:
        """
        Signal: engineer approved or rejected the remediation.

        Sent automatically from POST /api/v1/feedback when temporal_enabled=True.
        """
        self._approval_received = True
        self._approval_value = approved
        self._approval_comment = comment

    # ── Queries ───────────────────────────────────────────────────────────────

    @_workflow_query
    def approval_status(self) -> dict:
        """Query the current approval state without interrupting the workflow."""
        return {
            "approval_received": self._approval_received,
            "approved": self._approval_value if self._approval_received else None,
            "comment": self._approval_comment,
        }

    # ── Run ───────────────────────────────────────────────────────────────────

    @_workflow_run
    async def run(self, wf_input: RemediationInput) -> RemediationResult:
        """
        Execute the full remediation state machine.

        Steps
        ─────
        1. analyze_incident_activity   → creates Incident row
        2. generate_embedding_activity → stores semantic embedding (P-F2)
        3. notify_human_review_activity → alerts engineer (if require_approval)
        4. wait_condition              → waits for receive_approval signal
        5. score_remediation_activity  → scores Langfuse trace (P-F1)
        """
        from responseiq.temporal.activities import (
            ALL_ACTIVITIES,  # noqa: F401 — ensures activities registered
            analyze_incident_activity,
            generate_embedding_activity,
            notify_human_review_activity,
            score_remediation_activity,
        )

        result = RemediationResult(
            log_id=wf_input.log_id,
            approval_required=wf_input.require_approval,
        )

        retry = RetryPolicy(maximum_attempts=3) if _HAS_TEMPORAL else None
        activity_kwargs: dict = {
            "start_to_close_timeout": timedelta(minutes=5),
        }
        if retry is not None:
            activity_kwargs["retry_policy"] = retry

        # Step 1: Analyse
        await workflow.execute_activity(
            analyze_incident_activity,
            wf_input.log_id,
            **activity_kwargs,
        )
        result.analyzed = True
        result.workflow_steps.append("analyzed")

        # Step 2: Generate embedding (P-F2)
        await workflow.execute_activity(
            generate_embedding_activity,
            wf_input.log_id,
            start_to_close_timeout=timedelta(minutes=2),
        )
        result.embedding_stored = True
        result.workflow_steps.append("embedding_stored")

        # Step 3: Notify human (if required)
        if wf_input.require_approval and wf_input.notify_on_start:
            await workflow.execute_activity(
                notify_human_review_activity,
                args=[wf_input.log_id, f"Review requested for log_id={wf_input.log_id}"],
                start_to_close_timeout=timedelta(minutes=1),
            )
            result.workflow_steps.append("notified")

        # Step 4: Wait for human approval signal
        if wf_input.require_approval:
            met = await workflow.wait_condition(
                lambda: self._approval_received,
                timeout=timedelta(hours=wf_input.approval_timeout_hours),
            )
            if met:
                result.approved = self._approval_value
                result.workflow_steps.append("approved" if self._approval_value else "rejected")
            else:
                result.timed_out = True
                result.workflow_steps.append("timed_out")

        # Step 5: Score Langfuse (P-F1 flywheel)
        if result.approved is not None:
            await workflow.execute_activity(
                score_remediation_activity,
                args=[wf_input.log_id, result.approved, self._approval_comment],
                start_to_close_timeout=timedelta(minutes=1),
            )
            result.workflow_steps.append("scored")

        return result
