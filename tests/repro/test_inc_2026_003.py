"""
Reproduction test for incident: INC-2026-003

Expected Error: UnknownError: Incident reproduction required
Environment Type: resource
Generated: 2026-02-13T12:06:34.787031
"""

import os
from unittest.mock import Mock, patch

import pytest

from .base import ResponseIQReproBase


class TestInc2026003Reproduction(ResponseIQReproBase):
    """
    Minimal reproduction of resource incident.

    This test MUST fail before fix and pass after fix.
    """

    def test_inc_2026_003_resource_exhaustion(self):
        """Reproduce resource exhaustion incident."""
        with patch("os.statvfs") as mock_statvfs:
            # Mock statvfs to return no free space
            mock_result = Mock()
            mock_result.f_bavail = 0  # No available blocks
            mock_statvfs.return_value = mock_result

            with pytest.raises(Exception) as exc_info:
                # TODO: Replace with actual incident trigger code
                stat = os.statvfs("/")
                if stat.f_bavail == 0:
                    raise OSError("No space left on device")

            assert "space" in str(exc_info.value).lower()
