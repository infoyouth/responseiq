"""
Base class for ResponseIQ reproduction tests (P2).

Provides common setup, mocking utilities, and environment abstractions
to speed up test generation and ensure consistency.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock

import pytest


class ResponseIQReproBase:
    """
    DRY Testing base class for all reproduction tests.

    Handles common setup for mock logs, environments, and dependencies
    to minimize boilerplate in generated reproduction tests.
    """

    @pytest.fixture(autouse=True)
    def setup_repro_environment(self):
        """Setup common test environment before each reproduction test."""
        # Create isolated temporary directory for each test
        self._temp_dir = tempfile.mkdtemp(prefix="responseiq_repro_")
        self._temp_path = Path(self._temp_dir)

        # Store original environment variables to restore later
        self._original_env = os.environ.copy()

        yield

        # Cleanup after test
        import shutil

        shutil.rmtree(self._temp_dir, ignore_errors=True)

        # Restore original environment
        os.environ.clear()
        os.environ.update(self._original_env)

    def create_mock_log_file(self, content: str, filename: str = "test.log") -> Path:
        """Create a temporary log file with specified content."""
        log_file = self._temp_path / filename
        log_file.write_text(content)
        return log_file

    def create_mock_config_file(
        self, config_data: Dict[str, Any], filename: str = "config.json", format_type: str = "json"
    ) -> Path:
        """Create a temporary configuration file."""
        config_file = self._temp_path / filename

        if format_type == "json":
            import json

            config_file.write_text(json.dumps(config_data, indent=2))
        elif format_type == "yaml":
            import yaml

            config_file.write_text(yaml.dump(config_data, default_flow_style=False))
        else:
            config_file.write_text(str(config_data))

        return config_file

    def create_readonly_file(self, content: str = "test", filename: str = "readonly.txt") -> Path:
        """Create a read-only file to trigger permission errors."""
        readonly_file = self._temp_path / filename
        readonly_file.write_text(content)
        readonly_file.chmod(0o444)  # Read-only permissions
        return readonly_file

    def create_missing_file_path(self, filename: str = "missing.txt") -> Path:
        """Return path to a file that doesn't exist (for FileNotFoundError tests)."""
        return self._temp_path / filename

    def set_mock_environment_variable(self, key: str, value: str):
        """Set environment variable for current test."""
        os.environ[key] = value

    def mock_disk_full(self) -> Mock:
        """Return a mock that simulates disk full condition."""
        mock_disk = Mock()
        mock_disk.free = 0
        mock_disk.total = 1000000
        mock_disk.used = 1000000
        return mock_disk

    def mock_network_timeout(self, timeout_seconds: float = 5.0) -> Mock:
        """Return a mock that simulates network timeout."""
        import requests

        mock = Mock()
        mock.side_effect = requests.exceptions.Timeout(f"Request timed out after {timeout_seconds} seconds")
        return mock

    def mock_connection_refused(self, host: str = "localhost", port: int = 8080) -> Mock:
        """Return a mock that simulates connection refused."""
        import requests

        mock = Mock()
        mock.side_effect = requests.exceptions.ConnectionError(f"Connection refused: {host}:{port}")
        return mock

    def mock_dns_failure(self, hostname: str = "example.com") -> Mock:
        """Return a mock that simulates DNS resolution failure."""
        import socket

        mock = Mock()
        mock.side_effect = socket.gaierror(f"Name or service not known: {hostname}")
        return mock

    def mock_import_error(self, missing_module: str) -> Mock:
        """Return a mock that simulates missing Python module."""
        mock = Mock()
        mock.side_effect = ModuleNotFoundError(f"No module named '{missing_module}'")
        return mock

    def mock_version_conflict(self, package: str, required: str, actual: str) -> Mock:
        """Return a mock that simulates package version conflict."""
        mock = Mock()
        mock.side_effect = ImportError(f"Package '{package}' version conflict: required {required}, got {actual}")
        return mock

    def assert_error_signature_matches(self, exception_info, expected_signature: str):
        """Assert that caught exception matches the expected incident signature."""
        actual_error = str(exception_info.value)

        # Basic substring match
        assert expected_signature.lower() in actual_error.lower(), (
            f"Error signature mismatch:\n" f"Expected: {expected_signature}\n" f"Actual: {actual_error}"
        )

    def get_incident_fixture(self, incident_type: str = "generic") -> Dict[str, Any]:
        """Return mock incident data for testing."""
        fixtures = {
            "generic": {
                "id": "test-incident-001",
                "severity": "medium",
                "description": "Generic test incident",
                "source": "test",
            },
            "network": {
                "id": "network-timeout-001",
                "severity": "high",
                "description": "Connection timeout to API endpoint http://api.service.com/health",
                "source": "monitoring",
            },
            "filesystem": {
                "id": "file-missing-001",
                "severity": "medium",
                "description": "FileNotFoundError: [Errno 2] No such file or directory: '/etc/config.json'",
                "source": "application",
            },
            "permission": {
                "id": "permission-denied-001",
                "severity": "high",
                "description": "PermissionError: [Errno 13] Permission denied: '/var/log/app.log'",
                "source": "application",
            },
        }

        return fixtures.get(incident_type, fixtures["generic"])

    @property
    def temp_dir(self) -> Path:
        """Access to the temporary directory for this test."""
        return self._temp_path
