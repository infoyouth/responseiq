# All tests for removed CLI async functions and legacy main() logic have been removed due to CLI refactor.

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

# Import at module level — avoids module-cache pollution in xdist workers
from responseiq.cli import _run_demo, main


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
