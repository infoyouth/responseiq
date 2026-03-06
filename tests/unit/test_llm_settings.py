"""
tests/unit/test_llm_settings.py

Unit tests for P2.2 — Configurable LLM model settings.
Verifies:
  - Default values for all new LLM fields
  - Environment variable overrides work correctly
  - LLM service uses the configured model names and token limits
  - scrub_enabled default is True (safe-by-default)
"""

from unittest.mock import AsyncMock, patch

import pytest

from responseiq.config.settings import Settings

# ---------------------------------------------------------------------------
# Default settings
# ---------------------------------------------------------------------------


class TestLLMSettingsDefaults:
    def test_analysis_model_default(self, monkeypatch):
        monkeypatch.delenv("LLM_ANALYSIS_MODEL", raising=False)
        s = Settings(_env_file=None)
        assert s.llm_analysis_model == "gpt-4o"

    def test_fast_model_default(self, monkeypatch):
        monkeypatch.delenv("LLM_FAST_MODEL", raising=False)
        s = Settings(_env_file=None)
        assert s.llm_fast_model == "gpt-4o-mini"

    def test_repro_model_default(self, monkeypatch):
        monkeypatch.delenv("LLM_REPRO_MODEL", raising=False)
        s = Settings(_env_file=None)
        assert s.llm_repro_model == "gpt-4o"

    def test_max_tokens_default(self):
        s = Settings()
        assert s.llm_max_tokens == 2000

    def test_repro_max_tokens_default(self):
        s = Settings()
        assert s.llm_repro_max_tokens == 1500

    def test_scrub_enabled_default_is_true(self):
        """Safe-by-default: scrubbing must be ON unless explicitly disabled."""
        s = Settings()
        assert s.scrub_enabled is True

    def test_local_llm_fallback_default_is_true(self):
        s = Settings()
        assert s.use_local_llm_fallback is True


# ---------------------------------------------------------------------------
# Environment variable overrides
# ---------------------------------------------------------------------------


class TestLLMSettingsEnvOverrides:
    def test_analysis_model_override(self, monkeypatch):
        monkeypatch.setenv("LLM_ANALYSIS_MODEL", "gpt-4-turbo")
        s = Settings()
        assert s.llm_analysis_model == "gpt-4-turbo"

    def test_fast_model_override(self, monkeypatch):
        monkeypatch.setenv("LLM_FAST_MODEL", "gpt-3.5-turbo")
        s = Settings()
        assert s.llm_fast_model == "gpt-3.5-turbo"

    def test_max_tokens_override(self, monkeypatch):
        monkeypatch.setenv("LLM_MAX_TOKENS", "4096")
        s = Settings()
        assert s.llm_max_tokens == 4096

    def test_scrub_disabled_override(self, monkeypatch):
        monkeypatch.setenv("SCRUB_ENABLED", "false")
        s = Settings()
        assert s.scrub_enabled is False

    def test_repro_max_tokens_override(self, monkeypatch):
        monkeypatch.setenv("LLM_REPRO_MAX_TOKENS", "3000")
        s = Settings()
        assert s.llm_repro_max_tokens == 3000


# ---------------------------------------------------------------------------
# LLM service uses configured model name (not hardcoded gpt-3.5-turbo)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_llm_service_uses_configured_analysis_model():
    """
    Verify _analyze_with_openai sends the model name from settings, not a
    hardcoded string.
    """
    from pydantic import SecretStr

    from responseiq.ai.llm_service import _analyze_with_openai
    from responseiq.ai.schemas import IncidentAnalysis
    from responseiq.config.settings import Settings

    mock_settings = Settings()
    mock_settings.llm_analysis_model = "gpt-4-turbo-custom"
    mock_settings.llm_max_tokens = 3333
    mock_settings.openai_api_key = SecretStr("sk-fake")

    mock_instructor = AsyncMock()
    mock_instructor.chat = AsyncMock()
    mock_instructor.chat.completions = AsyncMock()
    mock_instructor.chat.completions.create = AsyncMock(
        return_value=IncidentAnalysis(title="T", severity="low", description="d", remediation="r")
    )

    with patch("responseiq.ai.llm_service.settings", mock_settings):
        with patch("responseiq.ai.model_utils.settings", mock_settings):
            with patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_instructor):
                await _analyze_with_openai("some log text", "")

    mock_instructor.chat.completions.create.assert_called_once()
    call_kwargs = mock_instructor.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4-turbo-custom", (
        f"Expected 'gpt-4-turbo-custom' but got '{call_kwargs.get('model')}'"
    )
    assert call_kwargs["max_tokens"] == 3333


@pytest.mark.asyncio
async def test_llm_service_uses_configured_repro_model():
    """
    Verify generate_reproduction_code uses llm_repro_model, not a hardcoded value.
    """
    from pydantic import SecretStr

    from responseiq.ai.llm_service import generate_reproduction_code
    from responseiq.ai.schemas import ReproductionCode
    from responseiq.config.settings import Settings

    mock_settings = Settings()
    mock_settings.llm_repro_model = "o3-mini"
    mock_settings.llm_repro_max_tokens = 2048
    mock_settings.openai_api_key = SecretStr("sk-fake")

    mock_instructor = AsyncMock()
    mock_instructor.chat = AsyncMock()
    mock_instructor.chat.completions = AsyncMock()
    mock_instructor.chat.completions.create = AsyncMock(return_value=ReproductionCode(code="def test_repro(): pass"))

    with patch("responseiq.ai.llm_service.settings", mock_settings):
        with patch("responseiq.ai.model_utils.settings", mock_settings):
            with patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_instructor):
                await generate_reproduction_code("NullPointerError in worker", "def worker(): pass")

    mock_instructor.chat.completions.create.assert_called_once()
    call_kwargs = mock_instructor.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "o3-mini"
    assert call_kwargs["max_tokens"] == 2048


@pytest.mark.asyncio
async def test_no_hardcoded_gpt35_in_analysis_path():
    """
    Regression guard: gpt-3.5-turbo must never be sent to OpenAI from the
    analysis path once this feature is shipped.
    """
    from pydantic import SecretStr

    from responseiq.ai.llm_service import _analyze_with_openai
    from responseiq.ai.schemas import IncidentAnalysis
    from responseiq.config.settings import Settings

    mock_settings = Settings()
    mock_settings.openai_api_key = SecretStr("sk-fake")

    mock_instructor = AsyncMock()
    mock_instructor.chat = AsyncMock()
    mock_instructor.chat.completions = AsyncMock()
    mock_instructor.chat.completions.create = AsyncMock(
        return_value=IncidentAnalysis(title="T", severity="low", description="d", remediation="r")
    )

    with patch("responseiq.ai.llm_service.settings", mock_settings):
        with patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_instructor):
            await _analyze_with_openai("test log", "")

    call_kwargs = mock_instructor.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] != "gpt-3.5-turbo", "REGRESSION: gpt-3.5-turbo is hardcoded again in the analysis path!"
