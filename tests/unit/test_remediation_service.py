from unittest.mock import AsyncMock, patch

import pytest

from responseiq.services.remediation_service import RemediationService


@pytest.fixture
def remediation_service():
    return RemediationService()


@pytest.mark.asyncio
async def test_remediate_incident_success(remediation_service):
    incident = {"log_content": "Error in main.py", "reason": "Crash"}
    context_path = "/tmp"

    mock_analysis = {"title": "Main Crash", "remediation": "Fix the bug on line 10"}

    with patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_analysis

        result = await remediation_service.remediate_incident(incident, context_path)

        assert result is True
        mock_analyze.assert_called_once_with("Error in main.py")


@pytest.mark.asyncio
async def test_remediate_incident_no_analysis(remediation_service):
    incident = {"reason": "Crash"}
    context_path = "/tmp"

    with patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = None

        result = await remediation_service.remediate_incident(incident, context_path)

        assert result is False


@pytest.mark.asyncio
async def test_remediate_incident_no_remediation_plan(remediation_service):
    incident = {"reason": "Crash"}
    context_path = "/tmp"

    # LLM returns analysis but no remediation steps
    mock_analysis = {"title": "Mystery Crash", "remediation": None}

    with patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_analysis

        result = await remediation_service.remediate_incident(incident, context_path)

        assert result is False
