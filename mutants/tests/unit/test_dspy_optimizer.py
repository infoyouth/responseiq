"""
Unit tests for src/responseiq/ai/dspy_optimizer.py

Coverage:
    is_available — returns False when dspy not installed          1 test
    is_available — returns False when dspy_enabled=False          1 test
    _load_fixtures — returns list from fixture directory          1 test
    _load_fixtures — handles missing fixture dir gracefully       1 test
    compile_prompts — skips and logs when not available           1 test
    load_compiled_program — returns None when not available       1 test
    load_compiled_program — returns None when no compiled file    1 test

Trust Gate:
    rationale    : feature-flagged; no-op when dspy not installed.
    blast_radius : compile writes only to ~/.responseiq/; no production paths.
    rollback_plan: set RESPONSEIQ_DSPY_ENABLED=false → all calls are no-ops.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from responseiq.ai.dspy_optimizer import (
    _load_fixtures,
    compile_prompts,
    is_available,
    load_compiled_program,
)


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    def test_returns_false_when_dspy_import_fails(self):
        # is_available() does lazy 'from responseiq.config.settings import settings'
        # and then 'import dspy'. Patch the config layer and force ImportError on dspy.
        mock_settings = MagicMock()
        mock_settings.dspy_enabled = True
        with (
            patch(
                "responseiq.config.settings.settings",
                mock_settings,
                create=True,
            ),
            patch.dict("sys.modules", {"dspy": None}),
        ):
            result = is_available()
        assert result is False

    def test_returns_false_when_dspy_disabled_in_settings(self):
        mock_settings = MagicMock()
        mock_settings.dspy_enabled = False
        with patch("responseiq.config.settings.settings", mock_settings, create=True):
            result = is_available()
        assert result is False


# ---------------------------------------------------------------------------
# _load_fixtures
# ---------------------------------------------------------------------------


class TestLoadFixtures:
    def test_returns_list_type(self):
        # Even with real fixtures dir the result must be a list (may be empty)
        result = _load_fixtures()
        assert isinstance(result, list)

    def test_returns_entries_with_message_or_log_keys(self):
        result = _load_fixtures()
        if result:
            # At least one example should have a text field
            keys_pool = {k for item in result for k in item}
            assert keys_pool & {"message", "log", "text", "expected_severity"}


# ---------------------------------------------------------------------------
# compile_prompts — no-op when unavailable
# ---------------------------------------------------------------------------


class TestCompilePrompts:
    def test_returns_none_when_not_available(self):
        with patch("responseiq.ai.dspy_optimizer.is_available", return_value=False):
            result = compile_prompts()
        assert result is None


# ---------------------------------------------------------------------------
# load_compiled_program — no-op paths
# ---------------------------------------------------------------------------


class TestLoadCompiledProgram:
    def test_returns_none_when_not_available(self):
        with patch("responseiq.ai.dspy_optimizer.is_available", return_value=False):
            result = load_compiled_program()
        assert result is None

    def test_returns_none_when_compiled_file_missing(self, tmp_path):
        # Point _COMPILED_PROGRAM_PATH to a non-existent file
        with (
            patch("responseiq.ai.dspy_optimizer.is_available", return_value=True),
            patch(
                "responseiq.ai.dspy_optimizer._COMPILED_PROGRAM_PATH",
                tmp_path / "nonexistent.json",
            ),
        ):
            result = load_compiled_program()
        assert result is None


# ---------------------------------------------------------------------------
# compile_prompts — full path when dspy is available (lines 87-153)
# ---------------------------------------------------------------------------


class TestCompilePromptsAvailable:
    def test_compile_runs_and_returns_path(self, tmp_path):
        compiled_path = tmp_path / "dspy_compiled.json"
        mock_dspy = MagicMock()
        mock_dspy.Signature = object  # 'class X(dspy.Signature)' becomes 'class X(object)'

        mock_settings_obj = MagicMock()
        mock_settings_obj.openai_api_key = MagicMock()
        mock_settings_obj.openai_api_key.get_secret_value.return_value = "sk-test"
        mock_settings_obj.llm_base_url = None

        fake_examples = [
            {"message": "ERROR: db timeout", "expected_severity": "high"},
            {"message": "WARNING: high memory", "expected_severity": "medium"},
            {"message": "CRITICAL: OOM kill", "expected_severity": "critical"},
        ]

        with (
            patch("responseiq.ai.dspy_optimizer.is_available", return_value=True),
            patch.dict("sys.modules", {"dspy": mock_dspy}),
            patch("responseiq.config.settings.settings", mock_settings_obj, create=True),
            patch("responseiq.ai.dspy_optimizer._COMPILED_PROGRAM_PATH", compiled_path),
            patch("responseiq.ai.dspy_optimizer._load_fixtures", return_value=fake_examples),
        ):
            result = compile_prompts()

        assert result == compiled_path
        mock_dspy.configure.assert_called_once()
        mock_dspy.BootstrapFewShot.assert_called_once()

    def test_compile_returns_none_when_no_openai_key_or_base_url(self, tmp_path):
        mock_dspy = MagicMock()
        mock_dspy.Signature = object

        mock_settings_obj = MagicMock()
        mock_settings_obj.openai_api_key = None
        mock_settings_obj.llm_base_url = None

        with (
            patch("responseiq.ai.dspy_optimizer.is_available", return_value=True),
            patch.dict("sys.modules", {"dspy": mock_dspy}),
            patch("responseiq.config.settings.settings", mock_settings_obj, create=True),
        ):
            result = compile_prompts()

        assert result is None


# ---------------------------------------------------------------------------
# load_compiled_program — when compiled file exists (lines 168-181)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _load_fixtures — list-format and missing-file branches (lines 51, 54)
# ---------------------------------------------------------------------------


class TestLoadFixturesBranches:
    def test_list_format_fixture_extends_examples(self):
        """When fixture JSON is a list, examples.extend() is used (line 54)."""
        fixture_json = '[{"message": "ERROR: disk full", "expected_severity": "high"}]'
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=fixture_json),
        ):
            from responseiq.ai.dspy_optimizer import _load_fixtures

            result = _load_fixtures()
        # 3 fixture files × 1 entry each = 3 total
        assert len(result) == 3
        assert result[0]["message"] == "ERROR: disk full"

    def test_missing_fixture_file_is_skipped(self):
        """When path.exists() returns False the file is skipped via continue (line 51)."""
        with patch("pathlib.Path.exists", return_value=False):
            from responseiq.ai.dspy_optimizer import _load_fixtures

            result = _load_fixtures()
        assert result == []


# ---------------------------------------------------------------------------
# is_available — ImportError with dspy_enabled=True hits line 69
# ---------------------------------------------------------------------------


class TestIsAvailableImportError:
    def test_returns_false_when_enabled_but_dspy_not_installed(self):
        """dspy_enabled=True + ImportError from dspy → return False at line 69."""
        with (
            patch("responseiq.config.settings.settings") as mock_s,
            patch.dict("sys.modules", {"dspy": None}),
        ):
            mock_s.dspy_enabled = True
            from responseiq.ai.dspy_optimizer import is_available

            assert is_available() is False


# ---------------------------------------------------------------------------
# compile_prompts — llm_base_url branch (line 96), too-few-examples (line 122),
# empty-log-field continue (lines 115-116)
# ---------------------------------------------------------------------------


class TestCompilePromptsEdgeCases:
    def test_uses_base_url_lm_when_no_openai_key(self):
        """When settings only has llm_base_url, use the openai/local LM path (line 96)."""
        mock_dspy = MagicMock()
        mock_dspy.Signature = object

        mock_s = MagicMock()
        mock_s.openai_api_key = None
        mock_s.llm_base_url = "http://localhost:11434/v1"

        fake_examples = [
            {"message": "ERROR: timeout", "expected_severity": "high"},
            {"message": "CRITICAL: oom", "expected_severity": "critical"},
        ]

        with (
            patch("responseiq.ai.dspy_optimizer.is_available", return_value=True),
            patch.dict("sys.modules", {"dspy": mock_dspy}),
            patch("responseiq.config.settings.settings", mock_s, create=True),
            patch("responseiq.ai.dspy_optimizer._load_fixtures", return_value=fake_examples),
        ):
            from responseiq.ai.dspy_optimizer import compile_prompts

            compile_prompts()

        # dspy.LM called with base_url (line 96 path)
        lm_calls = mock_dspy.LM.call_args_list
        base_url_call = any("local" in str(c) or "base_url" in str(c) for c in lm_calls)
        assert base_url_call

    def test_returns_none_when_all_examples_lack_log_field(self):
        """Examples with no message/log/text key are skipped; if < 2 remain, return None."""
        mock_dspy = MagicMock()
        mock_dspy.Signature = object

        mock_s = MagicMock()
        mock_s.openai_api_key = MagicMock()
        mock_s.openai_api_key.get_secret_value.return_value = "sk-test"
        mock_s.llm_base_url = None

        # Examples with no message/log/text → log="" → continue (lines 115-116)
        # Only 1 example has content → len(train_set) < 2 → return None (line 122)
        sparse_examples = [
            {"expected_severity": "high"},  # no log field
            {"expected_severity": "medium"},  # no log field
            {"message": "ERROR: only one real example", "expected_severity": "low"},
        ]

        with (
            patch("responseiq.ai.dspy_optimizer.is_available", return_value=True),
            patch.dict("sys.modules", {"dspy": mock_dspy}),
            patch("responseiq.config.settings.settings", mock_s, create=True),
            patch("responseiq.ai.dspy_optimizer._load_fixtures", return_value=sparse_examples),
        ):
            from responseiq.ai.dspy_optimizer import compile_prompts

            result = compile_prompts()

        assert result is None


class TestLoadCompiledProgramAvailable:
    def test_returns_loaded_program_when_file_present(self, tmp_path):
        compiled_path = tmp_path / "dspy_compiled.json"
        compiled_path.write_text("{}")

        mock_dspy = MagicMock()
        mock_dspy.Signature = object
        mock_program = MagicMock()
        mock_dspy.Predict.return_value = mock_program

        with (
            patch("responseiq.ai.dspy_optimizer.is_available", return_value=True),
            patch.dict("sys.modules", {"dspy": mock_dspy}),
            patch("responseiq.ai.dspy_optimizer._COMPILED_PROGRAM_PATH", compiled_path),
        ):
            result = load_compiled_program()

        assert result is not None
        mock_program.load.assert_called_once_with(str(compiled_path))
