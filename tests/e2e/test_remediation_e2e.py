"""
End-to-End tests for Trust Gate v1 remediation with policy enforcement.
Validates P1 roadmap requirements for safe, policy-governed remediation.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from responseiq.config.policy_config import (
    DenyReason,
    PolicyConfig,
    PolicyMode,
    SeverityThreshold,
    create_custom_policy,
)
from responseiq.services.remediation_service import RemediationService


class TestTrustGateE2E:
    """E2E tests for Trust Gate policy enforcement."""

    @pytest.fixture(autouse=True)
    def clean_artifacts(self):
        """Clean up generated reproduction files."""
        yield
        # Cleanup specific artifact ID
        artifact = Path("tests/repro/test_test_incident_001.py")
        if artifact.exists():
            artifact.unlink()

    @pytest.fixture
    def mock_ai_analysis(self):
        """Mock AI analysis result for testing."""
        return {
            "title": "Pod CrashLoopBackOff",
            "remediation": "Update deployment resource limits and restart",
            "confidence": 0.85,
            "rationale": "Memory limit too low causing OOM kills",
            "affected_files": ["k8s/deployment.yaml"],
            "proposed_changes": [
                {"file": "k8s/deployment.yaml", "type": "update", "changes": ["memory: 256Mi -> 512Mi"]}
            ],
        }

    @pytest.fixture
    def production_policy(self):
        """Production-like policy configuration."""
        return create_custom_policy(
            mode=PolicyMode.SUGGEST_ONLY,
            min_severity=SeverityThreshold.HIGH,
            min_confidence=0.8,
            min_impact_score=70.0,
            max_blast_radius="single_service",
            require_rollback_plan=True,
            require_test_plan=True,
        )

    @pytest.fixture
    def development_policy(self):
        """Development-friendly policy configuration."""
        return create_custom_policy(
            mode=PolicyMode.GUARDED_APPLY,
            min_severity=SeverityThreshold.LOW,
            min_confidence=0.5,
            min_impact_score=20.0,
            max_blast_radius="multi_service",
            require_rollback_plan=False,
            require_test_plan=False,
        )

    @pytest.fixture
    def critical_incident(self):
        """High-impact incident fixture that should pass most policies."""
        return {
            "id": "test-incident-001",
            "severity": "critical",
            "log_content": "OutOfMemoryError: Java heap space in critical-service",
            "reason": "Critical service pod killed due to OOM",
        }

    @pytest.fixture
    def low_impact_incident(self):
        """Low-impact incident that might be blocked by strict policies."""
        return {
            "id": "test-incident-002",
            "severity": "low",
            "log_content": "Warning: Deprecated API usage detected",
            "reason": "Using deprecated k8s API version",
        }

    @pytest.fixture
    def protected_path_incident(self):
        """Incident affecting protected paths."""
        return {
            "id": "test-incident-003",
            "severity": "critical",
            "log_content": "Configuration error in /etc/kubernetes/admin.conf",
            "reason": "K8s admin config corruption",
        }

    @pytest.mark.asyncio
    async def test_production_policy_blocks_low_severity(
        self, production_policy, low_impact_incident, mock_ai_analysis
    ):
        """
        E2E: Production policy should block low severity incidents.
        P1 requirement: severity threshold enforcement.
        """
        # Use AsyncMock for proper async function mocking

        with (
            patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
            patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
        ):
            mock_analyze.return_value = mock_ai_analysis
            mock_api_key.get_secret_value.return_value = "test-key"

            service = RemediationService(environment="test")
            service.trust_gate.update_policy(production_policy)

            recommendation = await service.remediate_incident(low_impact_incident)

            # Verify denial
            assert not recommendation.allowed
            assert recommendation.policy_validation.reason == DenyReason.SEVERITY_TOO_LOW
            assert "severity 'low' below minimum threshold 'high'" in recommendation.policy_validation.message
            assert "Escalate to severity >= high" in recommendation.required_actions

    @pytest.mark.asyncio
    async def test_development_policy_allows_low_severity(
        self, development_policy, low_impact_incident, mock_ai_analysis
    ):
        """
        E2E: Development policy should allow low severity incidents.
        P1 requirement: environment-specific policy enforcement.
        """
        # Use AsyncMock for proper async function mocking

        with (
            patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
            patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
        ):
            mock_analyze.return_value = mock_ai_analysis
            mock_api_key.get_secret_value.return_value = "test-key"

            service = RemediationService(environment="test")
            service.trust_gate.update_policy(development_policy)

            with (
                patch.object(service.trust_gate, "_run_security_scan", return_value=True),
                patch.object(service.trust_gate, "_run_syntax_check", return_value=True),
                patch.object(service.trust_gate, "_run_tests", return_value=True),
            ):

                recommendation = await service.remediate_incident(low_impact_incident)

                # Verify approval
                assert recommendation.allowed
                assert recommendation.execution_mode == PolicyMode.GUARDED_APPLY
                assert recommendation.confidence >= development_policy.min_confidence

    @pytest.mark.asyncio
    async def test_protected_paths_enforcement(self, development_policy, protected_path_incident):
        """
        E2E: Protected paths should be blocked regardless of other factors.
        P1 requirement: deterministic protected path rules.
        """
        mock_analysis = {
            "title": "Kubernetes Config Corruption",
            "remediation": "Restore k8s admin config from backup",
            "confidence": 0.95,
            "affected_files": ["/etc/kubernetes/admin.conf"],
            "rationale": "Critical k8s config file corrupted",
        }

        # Use AsyncMock for proper async function mocking

        with (
            patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
            patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
        ):
            mock_analyze.return_value = mock_analysis
            mock_api_key.get_secret_value.return_value = "test-key"

            service = RemediationService(environment="test")
            service.trust_gate.update_policy(development_policy)

            recommendation = await service.remediate_incident(protected_path_incident)

            # Verify denial due to protected path
            assert not recommendation.allowed
            assert recommendation.policy_validation.reason == DenyReason.PROTECTED_PATH
            assert "/etc/kubernetes/admin.conf" in recommendation.policy_validation.message
            assert "matches protected path pattern" in recommendation.policy_validation.message

    @pytest.mark.asyncio
    async def test_missing_rollback_plan_enforcement(self, production_policy, critical_incident, mock_ai_analysis):
        """
        E2E: Missing rollback plan should be blocked when required.
        P1 requirement: rollback plan validation.
        """
        # Override mock to not generate rollback plan
        mock_analysis_no_rollback = mock_ai_analysis.copy()
        mock_analysis_no_rollback["rollback_plan"] = None

        # Use AsyncMock for proper async function mocking

        with (
            patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
            patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
            patch.object(RemediationService, "_generate_rollback_plan", return_value=None),
        ):
            mock_analyze.return_value = mock_analysis_no_rollback
            mock_api_key.get_secret_value.return_value = "test-key"

            service = RemediationService(environment="test")
            service.trust_gate.update_policy(production_policy)

            # Mock reproduction service to avoid confidence downgrade
            mock_proof = MagicMock()
            mock_proof.reproduction_test.repro_method = "llm_synthesis"
            service.reproduction_service.analyze_and_generate_reproduction = AsyncMock(return_value=mock_proof)

            recommendation = await service.remediate_incident(critical_incident)

            # Verify denial due to missing rollback plan
            assert not recommendation.allowed
            assert recommendation.policy_validation.reason == DenyReason.MISSING_EVIDENCE
            assert "Rollback plan is required but not provided" in recommendation.policy_validation.message
            assert "Provide executable rollback plan" in recommendation.required_actions

    @pytest.mark.asyncio
    async def test_failed_security_checks_enforcement(self, development_policy, critical_incident, mock_ai_analysis):
        """
        E2E: Failed security checks should block remediation.
        P1 requirement: deterministic safety checks.
        """
        # Use AsyncMock for proper async function mocking

        with (
            patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
            patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
        ):
            mock_analyze.return_value = mock_ai_analysis
            mock_api_key.get_secret_value.return_value = "test-key"

            service = RemediationService(environment="test")
            service.trust_gate.update_policy(development_policy)

            # Mock reproduction service to avoid confidence downgrade
            mock_proof = MagicMock()
            mock_proof.reproduction_test.repro_method = "llm_synthesis"
            mock_proof.reproduction_test.status = "FAILED_AS_EXPECTED"
            service.reproduction_service.analyze_and_generate_reproduction = AsyncMock(return_value=mock_proof)
            service.reproduction_service.execute_reproduction_test = AsyncMock(return_value=mock_proof)

            # Mock security scan failure
            with (
                patch.object(service.trust_gate, "_run_security_scan", return_value=False),
                patch.object(service.trust_gate, "_run_syntax_check", return_value=True),
                patch.object(service.trust_gate, "_run_tests", return_value=True),
            ):

                recommendation = await service.remediate_incident(critical_incident)

                # Verify denial due to failed checks
                assert not recommendation.allowed
                assert recommendation.policy_validation.reason == DenyReason.CHECKS_FAILED
                assert "security_scan" in recommendation.checks_failed
                assert "Fix failed checks: security_scan" in recommendation.required_actions

    @pytest.mark.asyncio
    async def test_confidence_threshold_enforcement(self, production_policy, critical_incident):
        """
        E2E: Low confidence should be blocked by production policy.
        P1 requirement: confidence threshold validation.
        """
        low_confidence_analysis = {
            "title": "Uncertain Issue",
            "remediation": "Possible fix but uncertain",
            "confidence": 0.4,  # Below production threshold of 0.8
            "rationale": "Analysis uncertain due to incomplete logs",
        }

        # Use AsyncMock for proper async function mocking

        with (
            patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
            patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
        ):
            mock_analyze.return_value = low_confidence_analysis
            mock_api_key.get_secret_value.return_value = "test-key"

            service = RemediationService(environment="test")
            service.trust_gate.update_policy(production_policy)

            # Mock reproduction service to avoid confidence downgrade
            mock_proof = MagicMock()
            mock_proof.reproduction_test.repro_method = "llm_synthesis"
            mock_proof.reproduction_test.status = "FAILED_AS_EXPECTED"
            service.reproduction_service.analyze_and_generate_reproduction = AsyncMock(return_value=mock_proof)
            service.reproduction_service.execute_reproduction_test = AsyncMock(return_value=mock_proof)

            recommendation = await service.remediate_incident(critical_incident)

            # Verify denial due to insufficient confidence
            assert not recommendation.allowed
            assert recommendation.policy_validation.reason == DenyReason.INSUFFICIENT_CONFIDENCE
            assert "Confidence score 0.4 below minimum threshold 0.8" in recommendation.policy_validation.message

    @pytest.mark.asyncio
    async def test_policy_mode_suggest_only_behavior(self, critical_incident, mock_ai_analysis):
        """
        E2E: SUGGEST_ONLY mode should allow but not execute.
        P1 requirement: policy mode differentiation.
        """
        suggest_only_policy = create_custom_policy(
            mode=PolicyMode.SUGGEST_ONLY,
            min_severity=SeverityThreshold.MEDIUM,
            min_confidence=0.6,
        )

        # Use AsyncMock for proper async function mocking

        with (
            patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
            patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
        ):
            mock_analyze.return_value = mock_ai_analysis
            mock_api_key.get_secret_value.return_value = "test-key"

            service = RemediationService(environment="test")
            service.trust_gate.update_policy(suggest_only_policy)

            # Mock reproduction service to avoid confidence downgrade
            mock_proof = MagicMock()
            mock_proof.reproduction_test.repro_method = "llm_synthesis"
            mock_proof.reproduction_test.status = "FAILED_AS_EXPECTED"
            service.reproduction_service.analyze_and_generate_reproduction = AsyncMock(return_value=mock_proof)
            service.reproduction_service.execute_reproduction_test = AsyncMock(return_value=mock_proof)

            with (
                patch.object(service.trust_gate, "_run_security_scan", return_value=True),
                patch.object(service.trust_gate, "_run_syntax_check", return_value=True),
                patch.object(service.trust_gate, "_run_tests", return_value=True),
            ):

                recommendation = await service.remediate_incident(critical_incident)

                # Verify allowed but in suggestion mode
                assert recommendation.allowed
                assert recommendation.execution_mode == PolicyMode.SUGGEST_ONLY
                assert "Review the suggested remediation plan" in recommendation.next_steps
                assert "Manually implement changes if approved" in recommendation.next_steps

    @pytest.mark.asyncio
    async def test_policy_mode_pr_only_behavior(self, critical_incident, mock_ai_analysis):
        """
        E2E: PR_ONLY mode should create PR workflow.
        P1 requirement: PR-first execution path.
        """
        pr_only_policy = create_custom_policy(
            mode=PolicyMode.PR_ONLY,
            min_severity=SeverityThreshold.MEDIUM,
            min_confidence=0.6,
        )

        # Use AsyncMock for proper async function mocking

        with (
            patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
            patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
        ):
            mock_analyze.return_value = mock_ai_analysis
            mock_api_key.get_secret_value.return_value = "test-key"

            service = RemediationService(environment="test")
            service.trust_gate.update_policy(pr_only_policy)

            # Mock reproduction service to avoid confidence downgrade
            mock_proof = MagicMock()
            mock_proof.reproduction_test.repro_method = "llm_synthesis"
            mock_proof.reproduction_test.status = "FAILED_AS_EXPECTED"
            service.reproduction_service.analyze_and_generate_reproduction = AsyncMock(return_value=mock_proof)
            service.reproduction_service.execute_reproduction_test = AsyncMock(return_value=mock_proof)

            with (
                patch.object(service.trust_gate, "_run_security_scan", return_value=True),
                patch.object(service.trust_gate, "_run_syntax_check", return_value=True),
                patch.object(service.trust_gate, "_run_tests", return_value=True),
            ):

                recommendation = await service.remediate_incident(critical_incident)

                # Verify PR workflow
                assert recommendation.allowed
                assert recommendation.execution_mode == PolicyMode.PR_ONLY
                assert "Create pull request with proposed changes" in recommendation.next_steps
                assert "Request code review from team lead" in recommendation.next_steps

    @pytest.mark.asyncio
    async def test_blast_radius_enforcement(self, production_policy, critical_incident):
        """
        E2E: Excessive blast radius should be blocked.
        P1 requirement: blast radius limits.
        """
        env_wide_analysis = {
            "title": "Cluster-wide DNS Failure",
            "remediation": "Replace cluster DNS configuration",
            "confidence": 0.9,
            "affected_files": ["k8s/coredns-config.yaml"],
            "blast_radius": "env_wide",  # Exceeds production limit
        }

        # Use AsyncMock for proper async function mocking

        with (
            patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
            patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
            patch("responseiq.services.impact.infer_affected_surface", return_value="env_wide"),
        ):
            mock_analyze.return_value = env_wide_analysis
            mock_api_key.get_secret_value.return_value = "test-key"

            service = RemediationService(environment="test")
            service.trust_gate.update_policy(production_policy)

            # Mock reproduction service to avoid confidence downgrade
            mock_proof = MagicMock()
            mock_proof.reproduction_test.repro_method = "llm_synthesis"
            service.reproduction_service.analyze_and_generate_reproduction = AsyncMock(return_value=mock_proof)

            recommendation = await service.remediate_incident(critical_incident)

            # Verify denial due to blast radius
            assert not recommendation.allowed
            assert recommendation.policy_validation.reason == DenyReason.BLOCKED_BY_POLICY
            assert "exceeds maximum allowed 'single_service'" in recommendation.policy_validation.message

    @pytest.mark.asyncio
    async def test_complete_validation_success_flow(self, development_policy, critical_incident, mock_ai_analysis):
        """
        E2E: Complete successful validation should provide full recommendation.
        P1 requirement: end-to-end trust gate flow.
        """
        # Use AsyncMock for proper async function mocking

        with (
            patch("responseiq.services.remediation_service.analyze_with_llm", new_callable=AsyncMock) as mock_analyze,
            patch(
                "responseiq.services.reproduction_service.generate_reproduction_code", new_callable=AsyncMock
            ) as mock_gen_repro,
            patch("responseiq.ai.llm_service.settings.openai_api_key") as mock_api_key,
        ):
            mock_analyze.return_value = mock_ai_analysis
            mock_gen_repro.return_value = "def test_repro(): assert False"
            mock_api_key.get_secret_value.return_value = "test-key"

            service = RemediationService(environment="test")
            service.trust_gate.update_policy(development_policy)

            # Mock all checks passing
            with (
                patch.object(service.trust_gate, "_run_security_scan", return_value=True),
                patch.object(service.trust_gate, "_run_syntax_check", return_value=True),
                patch.object(service.trust_gate, "_run_tests", return_value=True),
            ):

                recommendation = await service.remediate_incident(critical_incident)

                # Verify complete success
                assert recommendation.allowed
                assert recommendation.execution_mode == PolicyMode.GUARDED_APPLY
                assert recommendation.confidence >= development_policy.min_confidence
                assert recommendation.impact_score >= development_policy.min_impact_score
                assert len(recommendation.checks_passed) == 3
                assert len(recommendation.checks_failed) == 0
                assert recommendation.rollback_plan is not None
                assert recommendation.test_plan is not None
                assert recommendation.risk_assessment["validation_passed"] is True
                assert "Remediation approved for guarded execution" in recommendation.policy_validation.message


class TestTrustGatePolicyConfiguration:
    """Test policy configuration and rule validation."""

    def test_protected_path_pattern_matching(self):
        """Test protected path pattern matching logic."""
        policy = PolicyConfig()

        # Test system files
        is_protected, rule = policy.is_path_protected("/etc/kubernetes/config.yaml")
        assert is_protected
        assert rule.pattern == "/etc/*"

        # Test production files
        is_protected, rule = policy.is_path_protected("apps/production/deployment.yaml")
        assert is_protected
        assert rule.pattern == "*/production/*"

        # Test SQL files
        is_protected, rule = policy.is_path_protected("migrations/001_create_users.sql")
        assert is_protected
        assert rule.pattern == "*.sql"

        # Test safe files
        is_protected, rule = policy.is_path_protected("src/main.py")
        assert not is_protected
        assert rule is None

    def test_severity_threshold_validation(self):
        """Test severity threshold comparison logic."""
        policy = PolicyConfig(min_severity=SeverityThreshold.HIGH)

        assert policy.validate_severity("critical") is True
        assert policy.validate_severity("high") is True
        assert policy.validate_severity("medium") is False
        assert policy.validate_severity("low") is False
        assert policy.validate_severity("unknown") is False

    def test_confidence_threshold_validation(self):
        """Test confidence score validation."""
        policy = PolicyConfig(min_confidence=0.7)

        assert policy.validate_confidence(0.8) is True
        assert policy.validate_confidence(0.7) is True
        assert policy.validate_confidence(0.6) is False
        assert policy.validate_confidence(-0.1) is False

    def test_blast_radius_validation(self):
        """Test blast radius limit enforcement."""
        policy = PolicyConfig(max_blast_radius="multi_service")

        assert policy.validate_blast_radius("single_service") is True
        assert policy.validate_blast_radius("multi_service") is True
        assert policy.validate_blast_radius("env_wide") is False
        assert policy.validate_blast_radius("unknown") is False

    def test_custom_policy_creation(self):
        """Test custom policy configuration override."""
        custom_policy = create_custom_policy(
            mode=PolicyMode.PR_ONLY, min_confidence=0.9, max_blast_radius="single_service"
        )

        assert custom_policy.mode == PolicyMode.PR_ONLY
        assert custom_policy.min_confidence == 0.9
        assert custom_policy.max_blast_radius == "single_service"
        # Other values should remain default
        assert custom_policy.min_severity == SeverityThreshold.MEDIUM
