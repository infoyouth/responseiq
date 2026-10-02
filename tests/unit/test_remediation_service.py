from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from responseiq.config.policy_config import DEFAULT_POLICIES, PolicyMode
from responseiq.schemas.proof import ProofBundle, SourceContext, SourceReference
from responseiq.services.remediation_service import RemediationService


@pytest.fixture
def remediation_service():
    return RemediationService()


def test_explicit_policy_mode_does_not_mutate_environment_default():
    service = RemediationService(environment="development", policy_mode=PolicyMode.PR_ONLY)

    assert service.trust_gate.policy.mode == PolicyMode.PR_ONLY
    assert DEFAULT_POLICIES["development"].mode == PolicyMode.GUARDED_APPLY


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
        mock_analyze.assert_called_once_with("Critical error in main.py", code_context="")


def test_remediation_normalizes_and_correlates_deployment_events(remediation_service):
    result = remediation_service._correlate_deployment_events(
        {
            "service": " Payments ",
            "commit_sha": "ABC123",
            "occurred_at": "2026-10-02T12:10:00Z",
            "deployment_events": [
                {
                    "event_id": "deploy-123",
                    "kind": "deployment",
                    "occurred_at": "2026-10-02T12:00:00Z",
                    "source": "test-provider",
                    "service": "payments",
                    "commit_sha": "abc123",
                }
            ],
        }
    )

    assert result is not None
    assert result.event.event_id == "deploy-123"
    assert result.relation == "correlated"
    assert {"service_match", "commit_sha_match"}.issubset(result.reasons)


@pytest.mark.asyncio
async def test_source_context_flows_through_remediation_and_proof(remediation_service):
    source_context = SourceContext(
        rendered="DETECTED SOURCE CODE CONTEXT: def handle(): return failure",
        references=[SourceReference(path="service.py", line_num=12, scope="handle")],
    )
    proof = ProofBundle(incident_id="context-incident", created_at=datetime.now())
    incident = {
        "id": "context-incident",
        "log_content": 'File "service.py", line 12, in handle: ValueError: failure',
        "severity": "critical",
    }
    mock_analysis = {
        "title": "Contextual failure",
        "remediation": "Fix handle",
        "confidence": 0.9,
        "rationale": "The source context identifies the failing function.",
    }

    with (
        patch("responseiq.services.remediation_service.extract_source_context", new_callable=AsyncMock) as mock_context,
        patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
        patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
    ):
        mock_context.return_value = source_context
        mock_analyze.return_value = mock_analysis
        mock_api_key.get_secret_value.return_value = "test-key"
        remediation_service.reproduction_service.analyze_and_generate_reproduction = AsyncMock(return_value=proof)
        remediation_service.reproduction_service.execute_reproduction_test = AsyncMock(return_value=proof)

        result = await remediation_service.remediate_incident(incident)

    mock_analyze.assert_called_once_with(incident["log_content"], code_context=source_context.rendered)
    reproduction_context = remediation_service.reproduction_service.analyze_and_generate_reproduction.call_args.kwargs[
        "context"
    ]
    assert reproduction_context["source_context"] == source_context.to_dict()
    assert result.evidence["source_context"] == source_context.to_dict()
    assert result.proof_bundle is proof
    assert proof.source_context is source_context


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
