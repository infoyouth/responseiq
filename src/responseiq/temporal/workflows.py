"""
src/responseiq/temporal/workflows.py

RemediationWorkflow — Temporal durable workflow for ResponseIQ (P-F4).

State machine
─────────────
  Detect → Context → [Notify] → [Wait: Human Approval] → Learn

The workflow is feature-flagged via ``settings.temporal_enabled = false``.
It is entirely inert until TEMPORAL_ENABLED=true AND a Temporal server is
reachable at TEMPORAL_HOST.

Activation
──────────
  1. Set TEMPORAL_ENABLED=true in .env
  2. Run Temporal server:  docker compose -f docker-compose.yml up temporal
  3. Start Temporal worker:  await start_temporal_worker()
  4. Submit workflow:
       client = await get_temporal_client()
       handle = await client.start_workflow(
           RemediationWorkflow.run,
           RemediationInput(log_id=42, require_approval=True),
           id=f"remediation-{log_id}",
           task_queue=settings.temporal_task_queue,
       )
  5. Approve via feedback endpoint (P-F1):
       POST /api/v1/feedback  {log_id: 42, approved: true}
       → sends RemediationWorkflow.receive_approval signal

Human approval signal integration (P-F1 ↔ P-F4)
─────────────────────────────────────────────────
  When settings.temporal_enabled=True, POST /api/v1/feedback calls:
      await handle.signal(RemediationWorkflow.receive_approval, True, comment)
  This wakes the waiting workflow and proceeds to the Learn step.

Determinism constraints (Temporal requirement)
──────────────────────────────────────────────
  Workflow code is replayed on worker restart.  All side effects MUST go
  in activities.  The workflow body only:
    - calls ``workflow.execute_activity(...)``
    - calls ``workflow.wait_condition(...)``
    - reads/writes instance variables
  Never import, log, or call external I/O directly inside workflow methods.
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
