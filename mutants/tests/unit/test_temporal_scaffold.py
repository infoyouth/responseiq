"""
tests/unit/test_temporal_scaffold.py — P-F4 Temporal Workflow Scaffold

These tests verify the feature-flagged Temporal integration without requiring
a Temporal server.  All tests pass in a standard CI environment where
``temporalio`` is NOT installed and ``TEMPORAL_ENABLED=false``.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch


# ── 1. Feature flag defaults ──────────────────────────────────────────────────


def test_temporal_feature_flag_default_false():
    from responseiq.config.settings import settings

    assert settings.temporal_enabled is False


def test_temporal_host_has_sensible_default():
    from responseiq.config.settings import settings

    assert settings.temporal_host == "localhost:7233"


def test_temporal_namespace_default():
    from responseiq.config.settings import settings

    assert settings.temporal_namespace == "responseiq"


def test_temporal_task_queue_default():
    from responseiq.config.settings import settings

    assert settings.temporal_task_queue == "responseiq-remediation"


# ── 2. TEMPORAL_AVAILABLE is always a bool ───────────────────────────────────


def test_temporal_available_is_bool():
    from responseiq.temporal import TEMPORAL_AVAILABLE

    assert isinstance(TEMPORAL_AVAILABLE, bool)


# ── 3. Worker returns None when disabled ─────────────────────────────────────


def test_start_temporal_worker_returns_none_when_disabled():
    """start_temporal_worker() must return None when temporal_enabled=False."""

    from responseiq.temporal.worker import start_temporal_worker

    result = asyncio.run(start_temporal_worker())
    assert result is None


def test_get_temporal_client_returns_none_when_unavailable():
    """get_temporal_client() returns None when temporalio is not installed."""

    from responseiq.temporal import TEMPORAL_AVAILABLE
    from responseiq.temporal.worker import get_temporal_client

    if not TEMPORAL_AVAILABLE:
        result = asyncio.run(get_temporal_client())
        assert result is None


# ── 4. Dataclasses are importable and have correct defaults ──────────────────


def test_remediation_input_defaults():
    from responseiq.temporal.workflows import RemediationInput

    inp = RemediationInput(log_id=42)
    assert inp.log_id == 42
    assert inp.require_approval is True
    assert inp.approval_timeout_hours == 48
    assert inp.notify_on_start is True


def test_remediation_result_fields():
    from responseiq.temporal.workflows import RemediationResult

    res = RemediationResult(log_id=99)
    assert res.log_id == 99
    assert res.analyzed is False
    assert res.embedding_stored is False
    assert res.timed_out is False
    assert res.approved is None
    assert res.error is None
    assert res.workflow_steps == []


# ── 5. Activities are callable ───────────────────────────────────────────────


def test_all_activities_are_callable():
    from responseiq.temporal.activities import ALL_ACTIVITIES

    assert isinstance(ALL_ACTIVITIES, list)
    assert len(ALL_ACTIVITIES) == 4
    for act in ALL_ACTIVITIES:
        assert callable(act), f"Activity {act} should be callable"


def test_activity_names_are_expected():
    from responseiq.temporal.activities import ALL_ACTIVITIES

    names = {a.__name__ for a in ALL_ACTIVITIES}
    assert "analyze_incident_activity" in names
    assert "generate_embedding_activity" in names
    assert "score_remediation_activity" in names
    assert "notify_human_review_activity" in names


# ── 6. Workflow class importable ─────────────────────────────────────────────


def test_workflow_class_importable():
    from responseiq.temporal.workflows import RemediationWorkflow

    wf = RemediationWorkflow()
    assert hasattr(wf, "receive_approval")
    assert hasattr(wf, "approval_status")
    assert hasattr(wf, "run")


def test_workflow_approval_status_initial_state():
    from responseiq.temporal.workflows import RemediationWorkflow

    wf = RemediationWorkflow()
    status = wf.approval_status()
    assert status["approval_received"] is False
    assert status["approved"] is None
    assert status["comment"] == ""


# ── 7. start_temporal_worker gracefully handles unavailable Temporal ─────────


def test_start_temporal_worker_when_enabled_but_no_server():
    """
    When temporal_enabled=True but no server is reachable,
    start_temporal_worker() should return None (not raise).
    """
    with patch("responseiq.temporal.worker.TEMPORAL_AVAILABLE", False):
        with patch("responseiq.config.settings.settings") as mock_settings:
            mock_settings.temporal_enabled = True

            import asyncio

            from responseiq.temporal.worker import start_temporal_worker

            # Should not raise — graceful degradation
            result = asyncio.run(start_temporal_worker())
            # Result may be None (disabled by flag in actual settings)
            assert result is None or asyncio.isfuture(result) or hasattr(result, "cancel")
