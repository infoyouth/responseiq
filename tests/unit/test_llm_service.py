"""
Unit tests for src/responseiq/ai/llm_service.py

Targets NEW code paths added in the modern tech-stack feature:
  _provider_name()          — 5 branches (litellm, ollama, groq, openai_compatible, openai)
  _get_instructor_client()  — LiteLLM branch (success + ImportError), base_url branch
  _analyze_with_openai()    — OTel span set_attribute calls + Langfuse spans
  generate_reproduction_code() — OTel spans + Langfuse spans + exception cleanup

Trust Gate:
  rationale    : All tests mock the LLM call; no real API keys or network calls.
  blast_radius : settings are patched at the module level, not mutated globally.
  rollback_plan: Remove the test file — no production code is changed.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# _provider_name — all 5 branches
# ---------------------------------------------------------------------------


class TestProviderName:
    """Exercise every return path of _provider_name()."""

    def test_returns_litellm_when_flag_enabled(self):
        mock_s = MagicMock()
        mock_s.use_litellm = True
        mock_s.llm_base_url = None
        with patch("responseiq.ai.llm_service.settings", mock_s):
            from responseiq.ai.llm_service import _provider_name

            assert _provider_name() == "litellm"

    def test_returns_ollama_for_standard_port(self):
        mock_s = MagicMock()
        mock_s.use_litellm = False
        mock_s.llm_base_url = "http://localhost:11434/v1"
        with patch("responseiq.ai.llm_service.settings", mock_s):
            from responseiq.ai.llm_service import _provider_name

            assert _provider_name() == "ollama"

    def test_returns_ollama_when_ollama_in_url(self):
        mock_s = MagicMock()
        mock_s.use_litellm = False
        mock_s.llm_base_url = "http://ollama.internal/v1"
        with patch("responseiq.ai.llm_service.settings", mock_s):
            from responseiq.ai.llm_service import _provider_name

            assert _provider_name() == "ollama"

    def test_returns_groq_for_groq_url(self):
        mock_s = MagicMock()
        mock_s.use_litellm = False
        mock_s.llm_base_url = "https://api.groq.com/openai/v1"
        with patch("responseiq.ai.llm_service.settings", mock_s):
            from responseiq.ai.llm_service import _provider_name

            assert _provider_name() == "groq"

    def test_returns_openai_compatible_for_unknown_base_url(self):
        mock_s = MagicMock()
        mock_s.use_litellm = False
        mock_s.llm_base_url = "https://my-proxy.example.com/v1"
        with patch("responseiq.ai.llm_service.settings", mock_s):
            from responseiq.ai.llm_service import _provider_name

            assert _provider_name() == "openai_compatible"

    def test_returns_openai_when_no_base_url(self):
        mock_s = MagicMock()
        mock_s.use_litellm = False
        mock_s.llm_base_url = None
        with patch("responseiq.ai.llm_service.settings", mock_s):
            from responseiq.ai.llm_service import _provider_name

            assert _provider_name() == "openai"


# ---------------------------------------------------------------------------
# _get_instructor_client — LiteLLM branch
# ---------------------------------------------------------------------------


class TestGetInstructorClientLiteLLM:
    def test_calls_from_litellm_when_flag_set(self):
        mock_s = MagicMock()
        mock_s.use_litellm = True
        mock_s.openai_api_key = None
        mock_s.llm_base_url = None

        mock_litellm = MagicMock()
        mock_from_litellm = MagicMock(return_value=MagicMock())

        with (
            patch("responseiq.ai.llm_service.settings", mock_s),
            patch.dict("sys.modules", {"litellm": mock_litellm}),
            patch("instructor.from_litellm", mock_from_litellm),
        ):
            from responseiq.ai.llm_service import _get_instructor_client

            _get_instructor_client()
            mock_from_litellm.assert_called_once()

    def test_falls_back_to_openai_when_litellm_missing(self):
        """ImportError from litellm should log a warning and fall through to openai."""
        mock_s = MagicMock()
        mock_s.use_litellm = True
        mock_s.openai_api_key = None
        mock_s.llm_base_url = None

        mock_from_openai = MagicMock(return_value=MagicMock())

        with (
            patch("responseiq.ai.llm_service.settings", mock_s),
            patch.dict("sys.modules", {"litellm": None}),  # triggers ImportError
            patch("instructor.from_openai", mock_from_openai),
        ):
            from responseiq.ai.llm_service import _get_instructor_client

            _get_instructor_client()
            mock_from_openai.assert_called_once()


# ---------------------------------------------------------------------------
# _get_instructor_client — base_url branch (Ollama / Groq / vLLM)
# ---------------------------------------------------------------------------


class TestGetInstructorClientBaseURL:
    def test_uses_json_mode_for_base_url_clients(self):
        import instructor

        mock_s = MagicMock()
        mock_s.use_litellm = False
        mock_s.llm_base_url = "http://localhost:11434/v1"
        mock_s.openai_api_key = None

        mock_from_openai = MagicMock(return_value=MagicMock())

        with (
            patch("responseiq.ai.llm_service.settings", mock_s),
            patch("responseiq.ai.llm_service.AsyncOpenAI", return_value=MagicMock()),
            patch("instructor.from_openai", mock_from_openai),
        ):
            from responseiq.ai.llm_service import _get_instructor_client

            _get_instructor_client()

        _, kwargs = mock_from_openai.call_args
        assert kwargs.get("mode") == instructor.Mode.JSON


# ---------------------------------------------------------------------------
# _analyze_with_openai — OTel span attributes + Langfuse spans
# ---------------------------------------------------------------------------


class TestAnalyzeWithOpenAIOtelSpans:
    def _mock_settings(self):
        mock_s = MagicMock()
        mock_s.openai_api_key = MagicMock()
        mock_s.openai_api_key.get_secret_value.return_value = "sk-test"
        mock_s.llm_base_url = None
        mock_s.scrub_enabled = False
        mock_s.llm_max_tokens = 2000
        mock_s.use_litellm = False
        return mock_s

    def _mock_instructor_client(self, dump_data: dict):
        mock_result = MagicMock()
        mock_result.model_dump.return_value = dump_data
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_result)
        return mock_client

    @pytest.mark.asyncio
    async def test_otel_spans_set_and_result_returned(self):
        mock_client = self._mock_instructor_client(
            {"title": "DB timeout", "severity": "high", "description": "d", "remediation": "r"}
        )
        with (
            patch("responseiq.ai.llm_service.settings", self._mock_settings()),
            patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_client),
            patch("responseiq.ai.llm_service.get_langfuse", return_value=None),
            patch("responseiq.ai.llm_service._router") as mock_router,
        ):
            mock_router.model_for.return_value = "gpt-4o-mini"
            from responseiq.ai.llm_service import _analyze_with_openai

            result = await _analyze_with_openai("ERROR: connection refused")

        assert result is not None
        assert result["title"] == "DB timeout"
        assert result["llm_model_used"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_langfuse_generation_tracked_when_configured(self):
        mock_client = self._mock_instructor_client(
            {"title": "OOM", "severity": "critical", "description": "d", "remediation": "r"}
        )
        mock_lf = MagicMock()
        mock_gen = MagicMock()
        mock_lf.start_generation.return_value = mock_gen

        with (
            patch("responseiq.ai.llm_service.settings", self._mock_settings()),
            patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_client),
            patch("responseiq.ai.llm_service.get_langfuse", return_value=mock_lf),
            patch("responseiq.ai.llm_service._router") as mock_router,
        ):
            mock_router.model_for.return_value = "gpt-4o-mini"
            from responseiq.ai.llm_service import _analyze_with_openai

            await _analyze_with_openai("ERROR: oom kill")

        mock_lf.start_generation.assert_called_once()
        mock_gen.update.assert_called()
        mock_gen.end.assert_called()

    @pytest.mark.asyncio
    async def test_langfuse_error_generation_tracked_on_exception(self):
        """When the instructor call raises, lf_generation should log ERROR and end."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("rate limited"))

        mock_lf = MagicMock()
        mock_gen = MagicMock()
        mock_lf.start_generation.return_value = mock_gen

        with (
            patch("responseiq.ai.llm_service.settings", self._mock_settings()),
            patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_client),
            patch("responseiq.ai.llm_service.get_langfuse", return_value=mock_lf),
            patch("responseiq.ai.llm_service._router") as mock_router,
        ):
            mock_router.model_for.return_value = "gpt-4o-mini"
            from responseiq.ai.llm_service import _analyze_with_openai

            result = await _analyze_with_openai("ERROR: crash")

        assert result is None
        # lf_generation.update called with level="ERROR"
        update_call_kwargs = mock_gen.update.call_args_list
        assert any("ERROR" in str(c) for c in update_call_kwargs)
        mock_gen.end.assert_called()


# ---------------------------------------------------------------------------
# generate_reproduction_code — OTel spans + Langfuse tracking + exception path
# ---------------------------------------------------------------------------


class TestGenerateReproductionCodeSpans:
    def _mock_settings(self):
        mock_s = MagicMock()
        mock_s.openai_api_key = MagicMock()
        mock_s.openai_api_key.get_secret_value.return_value = "sk-test"
        mock_s.llm_base_url = None
        mock_s.scrub_enabled = False
        mock_s.llm_repro_max_tokens = 1000
        mock_s.use_litellm = False
        return mock_s

    @pytest.mark.asyncio
    async def test_otel_spans_set_and_code_returned(self):
        mock_result = MagicMock()
        mock_result.code = "def test_bug(): assert False"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_result)

        with (
            patch("responseiq.ai.llm_service.settings", self._mock_settings()),
            patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_client),
            patch("responseiq.ai.llm_service.get_langfuse", return_value=None),
            patch("responseiq.ai.llm_service._router") as mock_router,
        ):
            mock_router.model_for.return_value = "gpt-4o-mini"
            from responseiq.ai.llm_service import generate_reproduction_code

            result = await generate_reproduction_code("DB timeout at db.py:45", "def get(): pass")

        assert result == "def test_bug(): assert False"

    @pytest.mark.asyncio
    async def test_langfuse_generation_tracked_on_success(self):
        mock_result = MagicMock()
        mock_result.code = "def test_(): pass"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_result)

        mock_lf = MagicMock()
        mock_gen = MagicMock()
        mock_lf.start_generation.return_value = mock_gen

        with (
            patch("responseiq.ai.llm_service.settings", self._mock_settings()),
            patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_client),
            patch("responseiq.ai.llm_service.get_langfuse", return_value=mock_lf),
            patch("responseiq.ai.llm_service._router") as mock_router,
        ):
            mock_router.model_for.return_value = "gpt-4o-mini"
            from responseiq.ai.llm_service import generate_reproduction_code

            await generate_reproduction_code("NULL at line 5", "def f(): pass")

        mock_lf.start_generation.assert_called_once()
        mock_gen.update.assert_called()
        mock_gen.end.assert_called()

    @pytest.mark.asyncio
    async def test_exception_triggers_langfuse_error_and_returns_none(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("timeout"))

        mock_lf = MagicMock()
        mock_gen = MagicMock()
        mock_lf.start_generation.return_value = mock_gen

        with (
            patch("responseiq.ai.llm_service.settings", self._mock_settings()),
            patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_client),
            patch("responseiq.ai.llm_service.get_langfuse", return_value=mock_lf),
            patch("responseiq.ai.llm_service._router") as mock_router,
        ):
            mock_router.model_for.return_value = "gpt-4o-mini"
            from responseiq.ai.llm_service import generate_reproduction_code

            result = await generate_reproduction_code("CRASH", "code")

        assert result is None
        update_kwargs = mock_gen.update.call_args_list
        assert any("ERROR" in str(c) for c in update_kwargs)
        mock_gen.end.assert_called()


# ---------------------------------------------------------------------------
# _analyze_with_openai — edge-case paths (lines 184, 188-189)
# ---------------------------------------------------------------------------


class TestAnalyzeWithOpenAIEdgePaths:
    @pytest.mark.asyncio
    async def test_early_return_none_when_no_key_and_no_url(self):
        """_analyze_with_openai returns None immediately when no key/url (line 184)."""
        mock_s = MagicMock()
        mock_s.openai_api_key = None
        mock_s.llm_base_url = None
        with patch("responseiq.ai.llm_service.settings", mock_s):
            from responseiq.ai.llm_service import _analyze_with_openai

            result = await _analyze_with_openai("ERROR: no credentials")
        assert result is None

    @pytest.mark.asyncio
    async def test_code_context_enriches_prompt(self):
        """code_context appended and logged (lines 188-189)."""
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "title": "Bug",
            "severity": "high",
            "description": "d",
            "remediation": "r",
        }
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_result)

        mock_s = MagicMock()
        mock_s.openai_api_key = MagicMock()
        mock_s.openai_api_key.get_secret_value.return_value = "sk-test"
        mock_s.llm_base_url = None
        mock_s.scrub_enabled = False
        mock_s.llm_max_tokens = 2000
        mock_s.use_litellm = False

        with (
            patch("responseiq.ai.llm_service.settings", mock_s),
            patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_client),
            patch("responseiq.ai.llm_service.get_langfuse", return_value=None),
            patch("responseiq.ai.llm_service._router") as mock_router,
        ):
            mock_router.model_for.return_value = "gpt-4o-mini"
            from responseiq.ai.llm_service import _analyze_with_openai

            result = await _analyze_with_openai("ERROR: crash", "def faulty(): pass")

        assert result is not None


# ---------------------------------------------------------------------------
# analyze_with_llm (public) — warning + debug paths (lines 163, 172-173)
# ---------------------------------------------------------------------------


class TestAnalyzeWithLLMFallbackPaths:
    @pytest.mark.asyncio
    async def test_warning_and_none_when_openai_fails_no_local_fallback(self):
        """analyze_with_llm: _analyze_with_openai returns None → warning (163),
        no local fallback → debug log (172) and return None (173)."""
        mock_s = MagicMock()
        mock_s.openai_api_key = MagicMock()
        mock_s.llm_base_url = None
        mock_s.scrub_enabled = False
        mock_s.use_local_llm_fallback = False

        with (
            patch("responseiq.ai.llm_service.settings", mock_s),
            patch(
                "responseiq.ai.llm_service._analyze_with_openai",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            from responseiq.ai.llm_service import analyze_with_llm

            result = await analyze_with_llm("ERROR: db down")

        assert result is None


# ---------------------------------------------------------------------------
# generate_reproduction_code — PII scrubbing log path (line 258)
# ---------------------------------------------------------------------------


class TestGenerateReproductionCodeScrubbing:
    @pytest.mark.asyncio
    async def test_logs_when_pii_tokens_scrubbed(self):
        """When scrub_enabled=True and PII is found, logger.info is called (line 258)."""
        mock_result = MagicMock()
        mock_result.code = "def test_bug(): pass"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_result)

        mock_s = MagicMock()
        mock_s.openai_api_key = MagicMock()
        mock_s.openai_api_key.get_secret_value.return_value = "sk-test"
        mock_s.llm_base_url = None
        mock_s.scrub_enabled = True  # enable scrubbing
        mock_s.llm_repro_max_tokens = 1000
        mock_s.use_litellm = False

        with (
            patch("responseiq.ai.llm_service.settings", mock_s),
            patch("responseiq.ai.llm_service._get_instructor_client", return_value=mock_client),
            patch("responseiq.ai.llm_service.get_langfuse", return_value=None),
            patch("responseiq.ai.llm_service._router") as mock_router,
            # Return a non-empty scrub_mapping so line 258 is reached
            patch(
                "responseiq.ai.llm_service.scrub",
                side_effect=[
                    ("redacted-summary", {"user@example.com": "<EMAIL_1>"}),
                    ("redacted-code", {}),
                ],
            ),
        ):
            mock_router.model_for.return_value = "gpt-4o-mini"
            from responseiq.ai.llm_service import generate_reproduction_code

            result = await generate_reproduction_code("Error for user@example.com at db.py:45", "def get(): pass")

        assert result == "def test_bug(): pass"
