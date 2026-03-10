"""
Unit tests for src/responseiq/services/critic_service.py

Coverage:
    review_remediation — no LLM key → None                     1 test
    review_remediation — timeout path → None                   1 test
    review_remediation — generic exception path → None         1 test
    review_remediation — happy path (mocked LLM) → str         1 test
    _CRITIC_SYSTEM_PROMPT / _CRITIC_USER_TEMPLATE content       2 tests

Trust Gate:
    rationale    : critic is advisory-only; every failure path returns None.
    blast_radius : only fast model is called; no writes to DB or filesystem.
    rollback_plan: set openai_api_key=None and llm_base_url=None → critic skips.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from types import SimpleNamespace
from unittest.mock import MagicMock

from responseiq.services.critic_service import (
    _CRITIC_SYSTEM_PROMPT,
    _CRITIC_USER_TEMPLATE,
    _call_critic_llm,
    review_remediation,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestCriticPromptConstants:
    def test_system_prompt_contains_format_hint(self):
        assert "LGTM" in _CRITIC_SYSTEM_PROMPT
        assert "WARNING" in _CRITIC_SYSTEM_PROMPT
        assert "CONCERN" in _CRITIC_SYSTEM_PROMPT

    def test_user_template_has_required_placeholders(self):
        rendered = _CRITIC_USER_TEMPLATE.format(incident_summary="test summary", proposed_fix="test fix")
        assert "test summary" in rendered
        assert "test fix" in rendered


# ---------------------------------------------------------------------------
# review_remediation — skip paths (no I/O)
# ---------------------------------------------------------------------------


class TestReviewRemediationSkipPaths:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_llm_configured(self):
        with (
            patch("responseiq.services.critic_service.settings") as mock_settings,
        ):
            mock_settings.openai_api_key = None
            mock_settings.llm_base_url = None
            result = await review_remediation("summary", "fix")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_timeout(self):
        async def _slow(*_args, **_kwargs):
            await asyncio.sleep(100)

        with (
            patch("responseiq.services.critic_service.settings") as mock_settings,
            patch("responseiq.services.critic_service._call_critic_llm", side_effect=_slow),
            patch("responseiq.services.critic_service._CRITIC_TIMEOUT_SECS", 0.01),
        ):
            mock_settings.openai_api_key = "sk-test"
            mock_settings.llm_base_url = None
            result = await review_remediation("summary", "fix")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_generic_exception(self):
        with (
            patch("responseiq.services.critic_service.settings") as mock_settings,
            patch(
                "responseiq.services.critic_service._call_critic_llm",
                side_effect=RuntimeError("boom"),
            ),
        ):
            mock_settings.openai_api_key = "sk-test"
            mock_settings.llm_base_url = None
            result = await review_remediation("summary", "fix")
        assert result is None


# ---------------------------------------------------------------------------
# review_remediation — happy path
# ---------------------------------------------------------------------------


class TestReviewRemediationHappyPath:
    @pytest.mark.asyncio
    async def test_returns_critique_string_from_llm(self):
        expected = "LGTM — the null-check is placed correctly."
        with (
            patch("responseiq.services.critic_service.settings") as mock_settings,
            patch(
                "responseiq.services.critic_service._call_critic_llm",
                new_callable=AsyncMock,
                return_value=expected,
            ),
        ):
            mock_settings.openai_api_key = "sk-test"
            mock_settings.llm_base_url = None
            result = await review_remediation("NullPointerException", "Add null check")
        assert result == expected
        assert result.startswith("LGTM")


# ---------------------------------------------------------------------------
# _call_critic_llm — internal LLM invocation (lines 82-141)
# ---------------------------------------------------------------------------


_FAKE_CRITIQUE = "LGTM — null-check is correctly placed before the call."


def _mock_critic_client(critique: str = _FAKE_CRITIQUE) -> MagicMock:
    """Return a mock instructor client that responds with critique."""
    mock_resp = SimpleNamespace(critique=critique)
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=mock_resp)
    return client


class TestCallCriticLLM:
    @pytest.mark.asyncio
    async def test_openai_branch_returns_critique(self):
        """Standard OpenAI path (no llm_base_url)."""
        mock_client = _mock_critic_client()
        with (
            patch("instructor.from_openai", return_value=mock_client),
            patch("responseiq.services.critic_service.settings") as mock_settings,
            patch("responseiq.services.critic_service._router") as mock_router,
            patch("responseiq.services.critic_service.get_langfuse", return_value=None),
        ):
            mock_settings.openai_api_key = MagicMock(get_secret_value=MagicMock(return_value="sk-test"))
            mock_settings.llm_base_url = None
            mock_router.model_for.return_value = "gpt-4o-mini"
            result = await _call_critic_llm("NullPointerException in PaymentService", "Add null check")
        assert result == _FAKE_CRITIQUE

    @pytest.mark.asyncio
    async def test_base_url_branch_uses_mode_json(self):
        """Custom base URL path (Ollama / Groq) uses instructor Mode.JSON."""
        mock_client = _mock_critic_client(critique="WARNING — test mode")
        mock_instructor = MagicMock()
        mock_instructor.from_openai.return_value = mock_client
        mock_instructor.Mode.JSON = "json"
        with (
            patch.dict("sys.modules", {"instructor": mock_instructor}),
            patch("responseiq.services.critic_service.settings") as mock_settings,
            patch("responseiq.services.critic_service._router") as mock_router,
            patch("responseiq.services.critic_service.get_langfuse", return_value=None),
        ):
            mock_settings.openai_api_key = MagicMock(get_secret_value=MagicMock(return_value="sk-test"))
            mock_settings.llm_base_url = "http://localhost:11434/v1"
            mock_router.model_for.return_value = "gpt-4o-mini"
            result = await _call_critic_llm("timeout in worker", "increase timeout")
        assert result == "WARNING — test mode"
        # Verify mode=JSON was passed
        _, call_kwargs = mock_instructor.from_openai.call_args
        assert call_kwargs.get("mode") == "json"

    @pytest.mark.asyncio
    async def test_langfuse_generation_is_tracked(self):
        """When Langfuse is configured, start_generation and end are called."""
        mock_client = _mock_critic_client()
        mock_lf_gen = MagicMock()
        mock_lf = MagicMock()
        mock_lf.start_generation.return_value = mock_lf_gen
        with (
            patch("instructor.from_openai", return_value=mock_client),
            patch("responseiq.services.critic_service.settings") as mock_settings,
            patch("responseiq.services.critic_service._router") as mock_router,
            patch("responseiq.services.critic_service.get_langfuse", return_value=mock_lf),
        ):
            mock_settings.openai_api_key = MagicMock(get_secret_value=MagicMock(return_value="sk-test"))
            mock_settings.llm_base_url = None
            mock_router.model_for.return_value = "gpt-4o-mini"
            await _call_critic_llm("DB timeout", "increase pool size")
        mock_lf.start_generation.assert_called_once()
        mock_lf_gen.end.assert_called_once()
