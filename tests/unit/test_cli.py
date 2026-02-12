import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from responseiq.cli import attempt_fix, process_file, scan_directory_async
from responseiq.utils.config_loader import ResponseIQConfig


@pytest.fixture
def mock_config():
    conf = MagicMock(spec=ResponseIQConfig)
    conf.ignored_dirs = {"ignore_me"}
    conf.ignored_extensions = {".ignored"}
    conf.is_ignored.side_effect = lambda p: p.name == "ignore_me" or p.suffix == ".ignored"
    return conf


@pytest.mark.asyncio
async def test_scan_directory_missing_path():
    """Test that scanning a missing directory logs error and exits."""
    with patch("responseiq.cli.sys.exit") as mock_exit:
        with patch("responseiq.cli.logger") as mock_logger:
            await scan_directory_async("/non/existent/path", "scan")

            mock_logger.error.assert_called_with("Target path /non/existent/path does not exist.")
            mock_exit.assert_called_with(1)


@pytest.mark.asyncio
async def test_scan_directory_no_valid_files(tmp_path, mock_config):
    """Test scanning a directory with only ignored files."""
    # Create ignored file
    (tmp_path / "test.ignored").touch()

    with patch("responseiq.cli.load_config", return_value=mock_config):
        with patch("responseiq.cli.logger") as mock_logger:
            await scan_directory_async(str(tmp_path), "scan")

            mock_logger.warning.assert_called()
            assert "No relevant log files found" in mock_logger.warning.call_args[0][0]


@pytest.mark.asyncio
async def test_scan_directory_with_issues(tmp_path, mock_config):
    """Test scanning a directory where issues are found."""
    # Create valid log file
    log_file = tmp_path / "app.log"
    log_file.write_text("Error: Something crashed")

    # Mock process_file to return an issue
    issue = {"file": str(log_file), "severity": "critical", "reason": "Crash detected", "status": "Detected"}

    with (
        patch("responseiq.cli.load_config", return_value=mock_config),
        patch("responseiq.cli.process_file", new_callable=AsyncMock) as mock_process,
        patch("responseiq.cli.sys.exit") as mock_exit,
    ):

        mock_process.return_value = issue

        # ACT
        await scan_directory_async(str(tmp_path), "scan")

        # ASSERT
        mock_process.assert_awaited_once()
        # Should exit 1 because issues found
        mock_exit.assert_called_with(1)


@pytest.mark.asyncio
async def test_process_file_no_keywords(tmp_path):
    """Test processing a file with no errors returns None."""
    log_file = tmp_path / "clean.log"
    log_file.write_text("Info: Application started. Everything is fine.")

    # Patch the class where it is DEFINED, so the local import picks up the mock
    with patch("responseiq.utils.log_processor.ParallelLogProcessor") as MockProcessorCls:
        mock_inst = MockProcessorCls.return_value
        mock_inst.scan_large_file = AsyncMock(return_value="Info: Application started.")

        result = await process_file(log_file, "scan")
        assert result is None


@pytest.mark.asyncio
async def test_process_file_detection(tmp_path):
    """Test processing a file with errors detects issue."""
    log_file = tmp_path / "error.log"
    # Content doesn't matter much if we mock, but path does

    with (
        patch("responseiq.utils.log_processor.ParallelLogProcessor") as MockProcessorCls,
        patch("responseiq.cli.analyze_message_async", new_callable=AsyncMock) as mock_analyzer,
    ):

        mock_inst = MockProcessorCls.return_value
        mock_inst.scan_large_file = AsyncMock(return_value="CRITICAL: Database connection failed panic")

        # Analyzer confirms it
        mock_analyzer.return_value = {"severity": "critical", "reason": "DB Failure"}

        result = await process_file(log_file, "scan")

        assert result is not None
        assert result["severity"] == "critical"
        assert result["reason"] == "DB Failure"
        assert result["status"] == "Detected"


@pytest.mark.asyncio
async def test_process_file_fix_mode(tmp_path):
    """Test fix mode triggers remediation."""
    log_file = tmp_path / "fixme.log"

    with (
        patch("responseiq.utils.log_processor.ParallelLogProcessor") as MockProcessorCls,
        patch("responseiq.cli.analyze_message_async", new_callable=AsyncMock) as mock_analyzer,
        patch("responseiq.cli.attempt_fix", new_callable=AsyncMock) as mock_attempt_fix,
    ):

        mock_inst = MockProcessorCls.return_value
        mock_inst.scan_large_file = AsyncMock(return_value="Error: Broken")

        # Must be high severity to trigger fix logic
        mock_analyzer.return_value = {"severity": "high", "reason": "broken"}

        # Mock fix success
        mock_attempt_fix.return_value = True

        result = await process_file(log_file, "fix")

        assert result is not None
        assert result["status"] == "Fixed"
        mock_attempt_fix.assert_awaited_once()


def test_main_help():
    """Test main prints help when no target found."""
    with (
        patch("sys.stdout"),
        patch("responseiq.cli.sys.exit") as mock_exit,
        patch("argparse.ArgumentParser.print_help"),
        patch("pathlib.Path.exists", return_value=False),
    ):  # No logging dir

        from responseiq.cli import main

        # Mock scan to ensure it's not called, or if it is, we know why
        with patch("responseiq.cli.scan_directory_async") as mock_scan:

            # Mock sys.exit to actually stop execution to verify correct exit code
            # But simpler: just assert the FIRST call was 0.
            # Because without side_effect, main() continues and crashes, calling exit(1) later.

            with patch.object(sys, "argv", ["responseiq"]):
                # We expect it to crash/continue if we don't raise,
                # so let's check call_args_list manually or simulate exit
                mock_exit.side_effect = SystemExit(0)

                try:
                    main()
                except SystemExit:
                    pass

                # Check that 0 was called
                mock_exit.assert_called_with(0)
                # Ensure we didn't try to scan
                mock_scan.assert_not_called()


def test_main_execution():
    """Test main runs scan when target provided."""
    with patch("responseiq.cli.scan_directory_async") as mock_scan, patch("responseiq.cli.sys.exit"):

        from responseiq.cli import main

        with patch.object(sys, "argv", ["responseiq", "--target", "/tmp/logs"]):
            main()

            mock_scan.assert_called_once()


@pytest.mark.asyncio
async def test_attempt_fix():
    """Test attempt_fix calls remediation service."""
    from responseiq.config.policy_config import PolicyMode
    from responseiq.services.remediation_service import RemediationRecommendation

    # Create a proper RemediationRecommendation mock object
    mock_recommendation = RemediationRecommendation(
        incident_id="test-1",
        title="Test Incident",
        severity="medium",
        confidence=0.8,
        impact_score=50.0,
        blast_radius="low",
        rationale="Test rationale",
        remediation_plan="Test plan",
        allowed=True,
        execution_mode=PolicyMode.SUGGEST_ONLY,
    )

    # We need to patch the global remediation_service instance in cli.py
    with patch("responseiq.cli.remediation_service.remediate_incident", new_callable=AsyncMock) as mock_remediate:
        mock_remediate.return_value = mock_recommendation

        issue = {"reason": "test"}
        path = Path("/tmp/file.log")

        success = await attempt_fix(path, issue)

        assert success is True
        mock_remediate.assert_awaited_once_with(issue, path.parent)
