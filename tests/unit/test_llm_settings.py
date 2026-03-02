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
    def test_analysis_model_default(self):
        s = Settings()
        assert s.llm_analysis_model == "gpt-4o"

    def test_fast_model_default(self):
        s = Settings()
        assert s.llm_fast_model == "gpt-4o-mini"

    def test_repro_model_default(self):
        s = Settings()
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
    captured: list[dict] = []

    async def fake_post(url, *, json=None, headers=None):
        captured.append(json or {})
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": '{"title":"T","severity":"low","description":"d","remediation":"r"}'}}]
        }
        return mock_resp

    from responseiq.ai.llm_service import _analyze_with_openai
    from responseiq.config.settings import Settings

    mock_settings = Settings()
    mock_settings.llm_analysis_model = "gpt-4-turbo-custom"
    mock_settings.llm_max_tokens = 3333

    with patch("responseiq.ai.llm_service.settings", mock_settings):
        # Give it a fake secret so the key check passes
        from pydantic import SecretStr

        mock_settings.openai_api_key = SecretStr("sk-fake")

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = fake_post
            mock_cls.return_value = mock_client

            await _analyze_with_openai("some log text", "")

    assert len(captured) == 1
    assert captured[0]["model"] == "gpt-4-turbo-custom", (
        f"Expected 'gpt-4-turbo-custom' but got '{captured[0].get('model')}'"
    )
    assert captured[0]["max_tokens"] == 3333


@pytest.mark.asyncio
async def test_llm_service_uses_configured_repro_model():
    """
    Verify generate_reproduction_code uses llm_repro_model, not a hardcoded value.
    """
    captured: list[dict] = []

    async def fake_post(url, *, json=None, headers=None):
        captured.append(json or {})
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": "def test_repro(): pass"}}]}
        return mock_resp

    from pydantic import SecretStr

    from responseiq.ai.llm_service import generate_reproduction_code
    from responseiq.config.settings import Settings

    mock_settings = Settings()
    mock_settings.llm_repro_model = "o3-mini"
    mock_settings.llm_repro_max_tokens = 2048
    mock_settings.openai_api_key = SecretStr("sk-fake")

    with patch("responseiq.ai.llm_service.settings", mock_settings):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = fake_post
            mock_cls.return_value = mock_client

            await generate_reproduction_code("NullPointerError in worker", "def worker(): pass")

    assert len(captured) == 1
    assert captured[0]["model"] == "o3-mini"
    assert captured[0]["max_tokens"] == 2048


@pytest.mark.asyncio
async def test_no_hardcoded_gpt35_in_analysis_path():
    """
    Regression guard: gpt-3.5-turbo must never be sent to OpenAI from the
    analysis path once this feature is shipped.
    """
    captured: list[dict] = []

    async def fake_post(url, *, json=None, headers=None):
        captured.append(json or {})
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": '{"title":"T","severity":"low","description":"d","remediation":"r"}'}}]
        }
        return mock_resp

    from pydantic import SecretStr

    from responseiq.ai.llm_service import _analyze_with_openai
    from responseiq.config.settings import Settings

    mock_settings = Settings()
    mock_settings.openai_api_key = SecretStr("sk-fake")

    with patch("responseiq.ai.llm_service.settings", mock_settings):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = fake_post
            mock_cls.return_value = mock_client

            await _analyze_with_openai("test log", "")

    assert len(captured) == 1
    assert captured[0]["model"] != "gpt-3.5-turbo", "REGRESSION: gpt-3.5-turbo is hardcoded again in the analysis path!"
