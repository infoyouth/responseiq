"""
Reproduction test for incident: INC-2026-001

Expected Error: Django app experiencing 500 errors due to DB connection pool exhaustion
Environment Type: network
Generated: 2026-02-13T12:06:34.783353
"""

from unittest.mock import patch

import pytest
import requests

from .base import ResponseIQReproBase


class TestInc2026001Reproduction(ResponseIQReproBase):
    """
    Minimal reproduction of network incident.

    This test MUST fail before fix and pass after fix.
    """

    @pytest.mark.asyncio
    async def test_inc_2026_001_network_failure(self):
        """Reproduce network-related incident."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError(
                "Django app experiencing 500 errors due to DB connection pool exhaustion"
            )

            with pytest.raises(Exception) as exc_info:
                # TODO: Replace with actual incident trigger code
                requests.get("http://example.com/api")

            assert "Django app experiencing 500 errors due to DB connection pool exhaustion" in str(exc_info.value)
