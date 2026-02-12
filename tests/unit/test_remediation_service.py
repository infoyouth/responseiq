from unittest.mock import AsyncMock, patch

import pytest

from responseiq.services.remediation_service import RemediationService


@pytest.fixture
def remediation_service():
    return RemediationService()


@pytest.mark.asyncio
async def test_remediate_incident_success(remediation_service):
    # High severity incident to pass policy requirements
    incident = {"log_content": "Critical error in main.py", "reason": "Crash", "severity": "critical"}
    context_path = "/tmp"

    # High confidence analysis to meet policy thresholds
    mock_analysis = {
        "title": "Critical Main Crash",
        "remediation": "Fix the bug on line 10",
        "confidence": 0.9,  # High confidence to pass policy
        "rationale": "Clear error pattern identified",
    }

    with (
        patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
        patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
    ):
        mock_analyze.return_value = mock_analysis
        mock_api_key.get_secret_value.return_value = "test-key"

        result = await remediation_service.remediate_incident(incident, context_path)

        # Verify we got a RemediationRecommendation object, not a boolean
        assert hasattr(result, "allowed"), "Expected RemediationRecommendation object"
        assert hasattr(result, "title"), "Expected RemediationRecommendation object"
        assert result.title == "Critical Main Crash"
        mock_analyze.assert_called_once_with("Critical error in main.py")


@pytest.mark.asyncio
async def test_remediate_incident_no_analysis(remediation_service):
    incident = {"reason": "Crash"}
    context_path = "/tmp"

    with (
        patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
        patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
    ):
        mock_analyze.return_value = None
        mock_api_key.get_secret_value.return_value = "test-key"

        result = await remediation_service.remediate_incident(incident, context_path)

        # Should return a RemediationRecommendation with fallback data when analysis fails
        assert hasattr(result, "allowed"), "Expected RemediationRecommendation object"
        assert hasattr(result, "title"), "Expected RemediationRecommendation object"
        assert result.title == "Remediation Failed"


@pytest.mark.asyncio
async def test_remediate_incident_no_remediation_plan(remediation_service):
    incident = {"reason": "Crash"}
    context_path = "/tmp"

    # LLM returns analysis but no remediation steps
    mock_analysis = {"title": "Mystery Crash", "remediation": None, "confidence": 0.9}

    with (
        patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
        patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
    ):
        mock_analyze.return_value = mock_analysis
        mock_api_key.get_secret_value.return_value = "test-key"

        result = await remediation_service.remediate_incident(incident, context_path)

        # Should return a RemediationRecommendation even when remediation plan is missing
        assert hasattr(result, "allowed"), "Expected RemediationRecommendation object"
        assert hasattr(result, "title"), "Expected RemediationRecommendation object"
        assert result.title == "Remediation Failed"
