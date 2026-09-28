"""tests/unit/test_llm_router.py

Unit tests for the P5.3 LLMRouter (src/responseiq/ai/model_utils.py).

Covers:
  - Default routing by task category (fast / patch / repro)
  - Reads live settings values (not cached stale models)
  - Explicit override() takes precedence over settings
  - Unknown task falls back to llm_analysis_model
  - table() returns full live snapshot with overrides applied
  - Module-level singleton is importable and functional
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from responseiq.ai.model_utils import FAST_TASKS, PATCH_TASKS, REPRO_TASKS, LLMRouter, router


# ── helpers ───────────────────────────────────────────────────────────────────


def _mock_settings(
    *,
    analysis: str = "gpt-4o",
    fast: str = "gpt-4o-mini",
    repro: str = "gpt-4o",
) -> object:
    """Return a simple namespace object that mimics the fields LLMRouter reads."""

    class _S:
        llm_analysis_model = analysis
        llm_fast_model = fast
        llm_repro_model = repro

    return _S()


# ── routing by category ────────────────────────────────────────────────────────


@pytest.mark.parametrize("task", sorted(FAST_TASKS))
def test_fast_tasks_use_fast_model(task: str) -> None:
    s = _mock_settings(fast="gpt-4o-mini", analysis="gpt-4o", repro="gpt-4o")
    with patch("responseiq.ai.model_utils.settings", s):
        r = LLMRouter()
        assert r.model_for(task) == "gpt-4o-mini"


@pytest.mark.parametrize("task", sorted(PATCH_TASKS))
def test_patch_tasks_use_analysis_model(task: str) -> None:
    s = _mock_settings(analysis="gpt-4o", fast="gpt-4o-mini")
    with patch("responseiq.ai.model_utils.settings", s):
        r = LLMRouter()
        assert r.model_for(task) == "gpt-4o"


@pytest.mark.parametrize("task", sorted(REPRO_TASKS))
def test_repro_tasks_use_repro_model(task: str) -> None:
    s = _mock_settings(repro="o3-mini", analysis="gpt-4o")
    with patch("responseiq.ai.model_utils.settings", s):
        r = LLMRouter()
        assert r.model_for(task) == "o3-mini"


# ── live settings are read on every call ──────────────────────────────────────


def test_model_for_reflects_live_settings() -> None:
    """model_for() must pick up settings changes without requiring a rebuild."""
    s1 = _mock_settings(analysis="gpt-4o")
    s2 = _mock_settings(analysis="claude-3-5-sonnet")
    r = LLMRouter()

    with patch("responseiq.ai.model_utils.settings", s1):
        assert r.model_for("analyze") == "gpt-4o"

    with patch("responseiq.ai.model_utils.settings", s2):
        assert r.model_for("analyze") == "claude-3-5-sonnet"


# ── explicit override ─────────────────────────────────────────────────────────


def test_override_wins_over_live_settings() -> None:
    s = _mock_settings(analysis="gpt-4o")
    r = LLMRouter()
    r.override("analyze", "claude-3-haiku")
    with patch("responseiq.ai.model_utils.settings", s):
        assert r.model_for("analyze") == "claude-3-haiku"


def test_override_does_not_affect_other_tasks() -> None:
    s = _mock_settings(analysis="gpt-4o", fast="gpt-4o-mini")
    r = LLMRouter()
    r.override("analyze", "custom-model")
    with patch("responseiq.ai.model_utils.settings", s):
        assert r.model_for("detect") == "gpt-4o-mini"


# ── unknown task fallback ─────────────────────────────────────────────────────


def test_unknown_task_falls_back_to_analysis_model() -> None:
    s = _mock_settings(analysis="gpt-4o")
    with patch("responseiq.ai.model_utils.settings", s):
        r = LLMRouter()
        assert r.model_for("completely_unknown_task") == "gpt-4o"


# ── table() snapshot ──────────────────────────────────────────────────────────


def test_table_returns_full_live_snapshot() -> None:
    s = _mock_settings(analysis="gpt-4o", fast="gpt-4o-mini", repro="o3-mini")
    with patch("responseiq.ai.model_utils.settings", s):
        r = LLMRouter()
        t = r.table()

    assert all(task in t for task in FAST_TASKS)
    assert all(task in t for task in PATCH_TASKS)
    assert all(task in t for task in REPRO_TASKS)
    assert t["detect"] == "gpt-4o-mini"
    assert t["analyze"] == "gpt-4o"
    assert t["generate_repro"] == "o3-mini"


def test_table_override_wins_in_snapshot() -> None:
    s = _mock_settings(analysis="gpt-4o")
    r = LLMRouter()
    r.override("analyze", "o3")
    with patch("responseiq.ai.model_utils.settings", s):
        t = r.table()
    assert t["analyze"] == "o3"


# ── module-level singleton ────────────────────────────────────────────────────


def test_module_singleton_is_llm_router() -> None:
    assert isinstance(router, LLMRouter)


def test_module_singleton_model_for_returns_string() -> None:
    result = router.model_for("analyze")
    assert isinstance(result, str)
    assert len(result) > 0
