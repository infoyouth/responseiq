# All tests for removed CLI async functions and legacy main() logic have been removed due to CLI refactor.

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

# Import at module level — avoids module-cache pollution in xdist workers
from responseiq.cli import _run_demo, _run_doctor, main


# ---------------------------------------------------------------------------
# _run_demo — fixture-present path
# ---------------------------------------------------------------------------
class TestRunDemoWithFixture:
    def test_runs_both_subprocess_calls(self, tmp_path, capsys):
        """With fixture present, demo runs scan then fix subprocess calls."""
        fixture_dir = tmp_path / "fixtures"
        fixture_dir.mkdir()
        (fixture_dir / "fixture_high.json").write_text(
            json.dumps([{"message": "ERROR: KeyError 'email' in process_user"}])
        )

        with (
            patch("responseiq.cli._find_project_root", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            _run_demo()

        assert mock_run.call_count == 2
        scan_args = mock_run.call_args_list[0][0][0]
        assert "--mode" in scan_args and "scan" in scan_args
        fix_args = mock_run.call_args_list[1][0][0]
        assert "--mode" in fix_args and "fix" in fix_args
        assert "--explain" in fix_args

    def test_output_contains_demo_header(self, tmp_path, capsys):
        fixture_dir = tmp_path / "fixtures"
        fixture_dir.mkdir()
        (fixture_dir / "fixture_high.json").write_text(json.dumps([{"message": "crash"}]))

        with (
            patch("responseiq.cli._find_project_root", return_value=tmp_path),
            patch("subprocess.run", return_value=MagicMock(returncode=0)),
        ):
            _run_demo()

        out = capsys.readouterr().out
        assert "ResponseIQ" in out
        assert "Demo complete" in out

    def test_fixture_alternative_keys_parsed(self, tmp_path):
        """Fixture using 'msg' key (not 'message') does not crash."""
        fixture_dir = tmp_path / "fixtures"
        fixture_dir.mkdir()
        (fixture_dir / "fixture_high.json").write_text(json.dumps([{"msg": "ALTERNATIVE_KEY_MSG"}]))

        with (
            patch("responseiq.cli._find_project_root", return_value=tmp_path),
            patch("subprocess.run", return_value=MagicMock(returncode=0)),
        ):
            _run_demo()  # must not raise


# ---------------------------------------------------------------------------
# _run_demo — hardcoded fallback (no fixture)
# ---------------------------------------------------------------------------
class TestRunDemoFallback:
    def test_fallback_when_no_fixture(self, tmp_path):
        """No fixtures/ dir → hardcoded fallback log is used; subprocess still called twice."""
        with (
            patch("responseiq.cli._find_project_root", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            _run_demo()

        assert mock_run.call_count == 2

    def test_fallback_output_has_demo_complete(self, tmp_path, capsys):
        with (
            patch("responseiq.cli._find_project_root", return_value=tmp_path),
            patch("subprocess.run", return_value=MagicMock(returncode=0)),
        ):
            _run_demo()

        out = capsys.readouterr().out
        assert "Demo complete" in out
        assert "docker logs" in out
        assert "kubectl logs" in out

    def test_subprocess_called_with_log_level_warning(self, tmp_path):
        """Both subprocess calls must include --log-level ERROR to suppress log noise in demo."""
        with (
            patch("responseiq.cli._find_project_root", return_value=tmp_path),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            _run_demo()

        for call in mock_run.call_args_list:
            args = call[0][0]
            assert "--log-level" in args
            assert "ERROR" in args


# ---------------------------------------------------------------------------
# main() — demo / init subcommand dispatch
# ---------------------------------------------------------------------------
class TestMainSubcommandDispatch:
    def test_demo_subcommand_calls_run_demo_and_exits(self, monkeypatch):
        """main() with 'demo' as argv[1] calls _run_demo and sys.exit(0)."""
        monkeypatch.setattr(sys, "argv", ["responseiq", "demo"])
        with patch("responseiq.cli._run_demo") as mock_demo:
            with pytest.raises(SystemExit) as exc_info:
                main()
        mock_demo.assert_called_once()
        assert exc_info.value.code == 0

    def test_init_subcommand_calls_run_init_and_exits(self, monkeypatch):
        """main() with 'init' as argv[1] calls _run_init and sys.exit(0)."""
        monkeypatch.setattr(sys, "argv", ["responseiq", "init"])
        with patch("responseiq.cli._run_init") as mock_init:
            with pytest.raises(SystemExit) as exc_info:
                main()
        mock_init.assert_called_once()
        assert exc_info.value.code == 0

    def test_doctor_reports_local_fallback(self, tmp_path, monkeypatch, capsys):
        """Doctor treats missing optional services as warnings, not failures."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'fixture'\n")
        monkeypatch.delenv("RESPONSEIQ_LLM_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        monkeypatch.delenv("RESPONSEIQ_OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("RESPONSEIQ_GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setattr("responseiq.cli._find_project_root", lambda: tmp_path)

        assert _run_doctor() == 0
        output = capsys.readouterr().out
        assert "LLM provider" in output
        assert "rule-engine fallback active" in output
        assert "Doctor complete" in output

    def test_doctor_checks_configured_llm_endpoint(self, tmp_path, monkeypatch, capsys):
        """Doctor checks the configured OpenAI-compatible endpoint."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'fixture'\n")
        monkeypatch.setenv("RESPONSEIQ_LLM_BASE_URL", "http://localhost:11434/v1")
        monkeypatch.setattr("responseiq.cli._find_project_root", lambda: tmp_path)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value = MagicMock()
            assert _run_doctor() == 0

        output = capsys.readouterr().out
        assert "LLM endpoint" in output
        assert "http://localhost:11434/v1/models" in output

    def test_doctor_reports_openai_provider(self, tmp_path, monkeypatch, capsys):
        """Doctor recognizes a configured hosted LLM provider."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'fixture'\n")
        monkeypatch.delenv("RESPONSEIQ_LLM_BASE_URL", raising=False)
        monkeypatch.setenv("RESPONSEIQ_OPENAI_API_KEY", "sk-test")
        monkeypatch.setattr("responseiq.cli._find_project_root", lambda: tmp_path)

        assert _run_doctor() == 0
        assert "OpenAI API key configured" in capsys.readouterr().out

    def test_doctor_reports_unsupported_endpoint_scheme(self, tmp_path, monkeypatch, capsys):
        """Doctor rejects non-HTTP endpoint schemes without making a request."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'fixture'\n")
        monkeypatch.setenv("RESPONSEIQ_LLM_BASE_URL", "ftp://localhost:11434/v1")
        monkeypatch.setattr("responseiq.cli._find_project_root", lambda: tmp_path)

        assert _run_doctor() == 0
        assert "unsupported URL scheme" in capsys.readouterr().out

    def test_doctor_reports_unreachable_endpoint(self, tmp_path, monkeypatch, capsys):
        """Doctor turns endpoint connection failures into actionable warnings."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'fixture'\n")
        monkeypatch.setenv("RESPONSEIQ_LLM_BASE_URL", "http://localhost:11434/v1")
        monkeypatch.setattr("responseiq.cli._find_project_root", lambda: tmp_path)

        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            assert _run_doctor() == 0

        assert "unreachable" in capsys.readouterr().out

    def test_doctor_blocks_missing_project_root(self, tmp_path, monkeypatch, capsys):
        """Doctor returns failure when run outside a project root."""
        monkeypatch.delenv("RESPONSEIQ_LLM_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        monkeypatch.delenv("RESPONSEIQ_OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("responseiq.cli._find_project_root", lambda: tmp_path)

        assert _run_doctor() == 1
        assert "blocking setup errors" in capsys.readouterr().out

    def test_run_init_smoke_test_subprocess_called(self, tmp_path):
        """_run_init runs a scan smoke-test subprocess when samples/crash.log exists and LLM != none."""
        from responseiq.cli import _run_init

        (tmp_path / "samples").mkdir()
        (tmp_path / "samples" / "crash.log").write_text("ERROR: crash\n")

        with (
            patch("responseiq.cli._find_project_root", return_value=tmp_path),
            # All interactive prompts return "" — falls through to 'ollama' branch (llm_provider != "none")
            patch("responseiq.cli._ask", return_value=""),
            patch("subprocess.run") as mock_sub,
        ):
            mock_sub.return_value = MagicMock(returncode=0)
            _run_init()

        assert mock_sub.called
        call_args = mock_sub.call_args[0][0]
        assert "--mode" in call_args and "scan" in call_args

    def test_demo_not_triggered_for_scan_mode(self, monkeypatch):
        """'--mode scan' does not trigger _run_demo."""
        monkeypatch.setattr(sys, "argv", ["responseiq", "--mode", "scan", "--target", "/tmp/x.log"])
        with (
            patch("responseiq.cli._run_demo") as mock_demo,
            patch("responseiq.cli.PluginRegistry") as mock_registry,
        ):
            mock_plugin = MagicMock()
            mock_plugin.run.return_value = None
            mock_registry.return_value.get_plugin.return_value = mock_plugin
            try:
                main()
            except SystemExit:
                pass
        mock_demo.assert_not_called()
