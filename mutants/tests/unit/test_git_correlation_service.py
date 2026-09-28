"""
tests/unit/test_git_correlation_service.py

Unit tests for P3 — Git Change-to-Incident Correlation.

Coverage
--------
- _extract_symbols()   : Python file paths, function names, exception types, etc.
- _parse_log_entries() : standard format, empty output, trailing-newline edge case
- CorrelationResult.to_dict() : round-trips via asdict
- GitCorrelationService.correlate() :
    - not a git repo          → graceful empty result
    - empty log window        → no_recent_commits=True
    - heuristic path          → suspect commit + confidence ≤ 0.75
    - LLM path (mocked)       → confidence upgraded, method="llm"
    - LLM returns non-JSON    → falls back to heuristic
    - LLM HTTP 500            → falls back to heuristic
- _heuristic_score()   : symbol overlap, no overlap, empty entries
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from responseiq.services.git_correlation_service import (
    CorrelationResult,
    GitCorrelationService,
    _extract_symbols,
    _parse_log_entries,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

SAMPLE_LOG_TEXT = """\
Traceback (most recent call last):
  File "/app/src/responseiq/services/payment_processor.py", line 42, in process_payment
    result = stripe_client.charge()
AttributeError: 'NoneType' object has no attribute 'charge'
ValueError: invalid literal for int() with base 10: 'abc'
"""

SAMPLE_GIT_LOG = """\
a1b2c3d Fix payment processor initialization
payment_processor.py
stripe_client.py
e4f5a6b Update README
README.md
"""

SAMPLE_DIFF = """\
diff --git a/payment_processor.py b/payment_processor.py
--- a/payment_processor.py
+++ b/payment_processor.py
@@ -40,6 +40,7 @@
+    if client is None:
+        raise ValueError("stripe_client not initialized")
"""


def _make_response(status: int, json_data: Dict[str, Any]) -> MagicMock:
    """Build a minimal mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data
    return resp


# ---------------------------------------------------------------------------
# _extract_symbols
# ---------------------------------------------------------------------------


class TestExtractSymbols:
    def test_python_file_path(self):
        symbols = _extract_symbols('  File "/app/src/responseiq/utils/helper.py", line 10, in foo')
        assert "helper" in symbols

    def test_function_name_in_frame(self):
        text = "  File 'foo.py', line 5, in process_payment"
        symbols = _extract_symbols(text)
        assert "process_payment" in symbols

    def test_exception_type(self):
        symbols = _extract_symbols("AttributeError: 'NoneType' object has no attribute 'x'")
        assert "AttributeError" in symbols

    def test_function_call_pattern(self):
        symbols = _extract_symbols("calling stripe_charge() returned None")
        assert "stripe_charge" in symbols

    def test_class_name_pattern(self):
        symbols = _extract_symbols("class StripeClient failed to initialize")
        assert "StripeClient" in symbols

    def test_filters_short_tokens(self):
        """Tokens shorter than 3 chars should be filtered out."""
        symbols = _extract_symbols("in ab() or File 'io.py'")
        for s in symbols:
            assert len(s) >= 3, f"Short token slipped through: {s!r}"

    def test_multiple_patterns_combined(self):
        symbols = _extract_symbols(SAMPLE_LOG_TEXT)
        assert "payment_processor" in symbols
        assert "ValueError" in symbols


# ---------------------------------------------------------------------------
# _parse_log_entries
# ---------------------------------------------------------------------------


class TestParseLogEntries:
    def test_standard_format(self):
        entries = _parse_log_entries(SAMPLE_GIT_LOG)
        assert len(entries) == 2

    def test_first_entry_sha_and_subject(self):
        entries = _parse_log_entries(SAMPLE_GIT_LOG)
        assert entries[0]["sha"] == "a1b2c3d"
        assert "payment processor" in entries[0]["subject"]

    def test_first_entry_files(self):
        entries = _parse_log_entries(SAMPLE_GIT_LOG)
        assert "payment_processor.py" in entries[0]["files"]
        assert "stripe_client.py" in entries[0]["files"]

    def test_empty_output(self):
        entries = _parse_log_entries("")
        assert entries == []

    def test_whitespace_only(self):
        entries = _parse_log_entries("\n\n  \n")
        assert entries == []

    def test_commit_with_no_files(self):
        log = "abc1234 Bump version\n"
        entries = _parse_log_entries(log)
        assert len(entries) == 1
        assert entries[0]["files"] == []


# ---------------------------------------------------------------------------
# CorrelationResult
# ---------------------------------------------------------------------------


class TestCorrelationResult:
    def test_to_dict_round_trip(self):
        cr = CorrelationResult(
            suspect_commit="abc1234 Fix bug",
            suspect_commit_sha="abc1234",
            confidence_score=0.65,
            suspect_files=["foo.py"],
            correlated_symbols=["FooError", "bar"],
            diff_summary="Changed foo.py line 10",
            lookback_hours=24,
            method="heuristic",
            rationale="Symbol overlap",
        )
        d = cr.to_dict()
        assert d["suspect_commit"] == "abc1234 Fix bug"
        assert d["confidence_score"] == 0.65
        assert d["suspect_files"] == ["foo.py"]
        assert d["method"] == "heuristic"

    def test_default_values(self):
        cr = CorrelationResult()
        assert cr.suspect_commit is None
        assert cr.confidence_score == 0.0
        assert cr.no_recent_commits is False
        assert cr.suspect_files == []


# ---------------------------------------------------------------------------
# GitCorrelationService.correlate() — integration-style with mocked git
# ---------------------------------------------------------------------------


class TestCorrelateNotAGitRepo:
    """run_with_output returns None (not a git repo)."""

    @pytest.mark.asyncio
    async def test_not_git_repo_returns_empty_result(self):
        svc = GitCorrelationService(repo_path=Path("/tmp"))
        with patch.object(svc._client, "run_with_output", return_value=None):
            result = await svc.correlate(log_text=SAMPLE_LOG_TEXT)

        assert result.suspect_commit is None
        assert result.confidence_score == 0.0
        assert result.no_recent_commits is False  # different flag from empty log


class TestCorrelateNoRecentCommits:
    """Git repo exists but no commits in the lookback window."""

    @pytest.mark.asyncio
    async def test_no_commits_sets_flag(self):
        svc = GitCorrelationService(repo_path=Path("/tmp"))
        with (
            patch.object(svc._client, "run_with_output", return_value=".git"),
            patch.object(svc._client, "get_log_entries", return_value=""),
        ):
            result = await svc.correlate(log_text=SAMPLE_LOG_TEXT, lookback_hours=1)

        assert result.no_recent_commits is True
        assert result.suspect_commit is None
        assert "1 hours" in result.rationale

    @pytest.mark.asyncio
    async def test_whitespace_log_treated_as_empty(self):
        svc = GitCorrelationService(repo_path=Path("/tmp"))
        with (
            patch.object(svc._client, "run_with_output", return_value=".git"),
            patch.object(svc._client, "get_log_entries", return_value="   \n  "),
        ):
            result = await svc.correlate(log_text=SAMPLE_LOG_TEXT)

        assert result.no_recent_commits is True


class TestCorrelateHeuristicPath:
    """Normal heuristic path with matching symbols."""

    @pytest.mark.asyncio
    async def test_heuristic_identifies_suspect_commit(self):
        svc = GitCorrelationService(repo_path=Path("/tmp"))
        with (
            patch.object(svc._client, "run_with_output", return_value=".git"),
            patch.object(svc._client, "get_log_entries", return_value=SAMPLE_GIT_LOG),
            # No openai key → stays on heuristic
            patch("responseiq.services.git_correlation_service.settings") as mock_settings,
        ):
            mock_settings.openai_api_key = None
            mock_settings.llm_fast_model = "gpt-4o-mini"
            result = await svc.correlate(log_text=SAMPLE_LOG_TEXT)

        assert result.suspect_commit is not None
        assert "a1b2c3d" in result.suspect_commit
        assert 0.0 < result.confidence_score <= 0.75
        assert result.method == "heuristic"

    @pytest.mark.asyncio
    async def test_heuristic_confidence_capped_at_0_75(self):
        """Even a perfect match should not exceed 0.75 in heuristic mode."""
        svc = GitCorrelationService(repo_path=Path("/tmp"))
        with (
            patch.object(svc._client, "run_with_output", return_value=".git"),
            patch.object(svc._client, "get_log_entries", return_value=SAMPLE_GIT_LOG),
            patch("responseiq.services.git_correlation_service.settings") as mock_settings,
        ):
            mock_settings.openai_api_key = None
            mock_settings.llm_fast_model = "gpt-4o-mini"
            result = await svc.correlate(log_text=SAMPLE_LOG_TEXT)

        assert result.confidence_score <= 0.75

    @pytest.mark.asyncio
    async def test_no_overlap_gives_zero_confidence(self):
        """Commits that touch unrelated files → no suspect commit identified."""
        unrelated_log = "d7e8f9a Update docs\nCHANGELOG.md\n"
        svc = GitCorrelationService(repo_path=Path("/tmp"))
        with (
            patch.object(svc._client, "run_with_output", return_value=".git"),
            patch.object(svc._client, "get_log_entries", return_value=unrelated_log),
            patch("responseiq.services.git_correlation_service.settings") as mock_settings,
        ):
            mock_settings.openai_api_key = None
            mock_settings.llm_fast_model = "gpt-4o-mini"
            result = await svc.correlate(log_text=SAMPLE_LOG_TEXT)

        # No overlap → confidence may be 0 (or very low if no match found)
        assert result.confidence_score == 0.0 or result.suspect_commit is None


# ---------------------------------------------------------------------------
# GitCorrelationService.correlate() — LLM path (mocked httpx)
# ---------------------------------------------------------------------------

_LLM_OK_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": json.dumps(
                    {
                        "suspect_commit_sha": "a1b2c3d",
                        "suspect_commit": "a1b2c3d Fix payment processor initialization",
                        "confidence_score": 0.91,
                        "suspect_files": ["payment_processor.py"],
                        "diff_summary": "The initialization guard was missing, causing NoneType errors.",
                        "rationale": "The diff shows the guard was added after the incident.",
                    }
                )
            }
        }
    ]
}


class TestLLMCorrelate:
    @pytest.mark.asyncio
    async def test_llm_upgrades_confidence(self):
        """LLM result should set method='llm' and allow confidence > 0.75."""
        svc = GitCorrelationService(repo_path=Path("/tmp"))
        with (
            patch.object(svc._client, "run_with_output", return_value=".git"),
            patch.object(svc._client, "get_log_entries", return_value=SAMPLE_GIT_LOG),
            patch.object(svc._client, "get_recent_diff", return_value=SAMPLE_DIFF),
            patch("responseiq.services.git_correlation_service.settings") as mock_settings,
            patch("httpx.AsyncClient") as mock_http,
        ):
            # Simulate OpenAI key present
            secret_mock = MagicMock()
            secret_mock.get_secret_value.return_value = "sk-test-key"
            mock_settings.openai_api_key = secret_mock
            mock_settings.llm_fast_model = "gpt-4o-mini"

            # Mock the HTTP call
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=_make_response(200, _LLM_OK_RESPONSE))
            mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_http.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await svc.correlate(log_text=SAMPLE_LOG_TEXT)

        assert result.method == "llm"
        assert result.confidence_score == pytest.approx(0.91)
        assert "payment_processor.py" in result.suspect_files

    @pytest.mark.asyncio
    async def test_llm_non_json_falls_back_to_heuristic(self):
        """Non-JSON LLM response → keep heuristic result, no crash."""
        bad_response = {"choices": [{"message": {"content": "Sorry, I cannot help with that."}}]}

        svc = GitCorrelationService(repo_path=Path("/tmp"))
        with (
            patch.object(svc._client, "run_with_output", return_value=".git"),
            patch.object(svc._client, "get_log_entries", return_value=SAMPLE_GIT_LOG),
            patch.object(svc._client, "get_recent_diff", return_value=SAMPLE_DIFF),
            patch("responseiq.services.git_correlation_service.settings") as mock_settings,
            patch("httpx.AsyncClient") as mock_http,
        ):
            secret_mock = MagicMock()
            secret_mock.get_secret_value.return_value = "sk-test-key"
            mock_settings.openai_api_key = secret_mock
            mock_settings.llm_fast_model = "gpt-4o-mini"

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=_make_response(200, bad_response))
            mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_http.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await svc.correlate(log_text=SAMPLE_LOG_TEXT)

        # Should NOT crash and should still return heuristic result
        assert result is not None
        assert result.method == "heuristic"

    @pytest.mark.asyncio
    async def test_llm_http_500_falls_back_to_heuristic(self):
        """HTTP 500 from OpenAI → keep heuristic result, no crash."""
        svc = GitCorrelationService(repo_path=Path("/tmp"))
        with (
            patch.object(svc._client, "run_with_output", return_value=".git"),
            patch.object(svc._client, "get_log_entries", return_value=SAMPLE_GIT_LOG),
            patch.object(svc._client, "get_recent_diff", return_value=SAMPLE_DIFF),
            patch("responseiq.services.git_correlation_service.settings") as mock_settings,
            patch("httpx.AsyncClient") as mock_http,
        ):
            secret_mock = MagicMock()
            secret_mock.get_secret_value.return_value = "sk-test-key"
            mock_settings.openai_api_key = secret_mock
            mock_settings.llm_fast_model = "gpt-4o-mini"

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=_make_response(500, {}))
            mock_http.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_http.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await svc.correlate(log_text=SAMPLE_LOG_TEXT)

        assert result is not None
        assert result.method == "heuristic"

    @pytest.mark.asyncio
    async def test_llm_empty_diff_skips_llm(self):
        """When git diff returns empty patch, LLM correlate exits early."""
        svc = GitCorrelationService(repo_path=Path("/tmp"))
        with (
            patch.object(svc._client, "run_with_output", return_value=".git"),
            patch.object(svc._client, "get_log_entries", return_value=SAMPLE_GIT_LOG),
            patch.object(svc._client, "get_recent_diff", return_value=""),
            patch("responseiq.services.git_correlation_service.settings") as mock_settings,
            patch("httpx.AsyncClient") as mock_http,
        ):
            secret_mock = MagicMock()
            secret_mock.get_secret_value.return_value = "sk-test-key"
            mock_settings.openai_api_key = secret_mock
            mock_settings.llm_fast_model = "gpt-4o-mini"

            result = await svc.correlate(log_text=SAMPLE_LOG_TEXT)

        # httpx should NOT have been called — staying heuristic
        mock_http.assert_not_called()
        assert result.method == "heuristic"


# ---------------------------------------------------------------------------
# Heuristic scorer edge cases
# ---------------------------------------------------------------------------


class TestHeuristicScore:
    def test_empty_entries(self):
        entry, score, files = GitCorrelationService._heuristic_score([], ["payment", "stripe"], "log text")
        assert entry is None
        assert score == 0.0
        assert files == []

    def test_symbol_overlap_scores_positively(self):
        entries = [{"sha": "aaa1111", "subject": "Fix payment bug", "files": ["payment_processor.py"]}]
        entry, score, files = GitCorrelationService._heuristic_score(
            entries, ["payment_processor", "stripe"], "payment_processor failed"
        )
        assert entry is not None
        assert entry["sha"] == "aaa1111"
        assert score > 0.0
        assert "payment_processor.py" in files

    def test_subject_line_bonus(self):
        entries = [
            {"sha": "bbb2222", "subject": "Refactor stripe_client initialization", "files": []},
        ]
        _, score_with_match, _ = GitCorrelationService._heuristic_score(
            entries, ["stripe_client"], "stripe_client crashed"
        )
        entries2 = [{"sha": "ccc3333", "subject": "Update README", "files": []}]
        _, score_no_match, _ = GitCorrelationService._heuristic_score(
            entries2, ["stripe_client"], "stripe_client crashed"
        )
        assert score_with_match > score_no_match
