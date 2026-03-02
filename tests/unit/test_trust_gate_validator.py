"""
Unit tests for Trust Gate Validator core validation logic.
Tests individual validation methods and decision-making logic.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from responseiq.config.policy_config import (
    DenyReason,
    PolicyMode,
    SeverityThreshold,
    create_custom_policy,
)
from responseiq.services.trust_gate import (
    RemediationRequest,
    TrustGateValidator,
    ValidationResult,
)


class TestTrustGateValidatorCore:
    """Test core trust gate validation logic."""

    @pytest.fixture
    def basic_policy(self):
        """Basic policy configuration for testing."""
        return create_custom_policy(
            mode=PolicyMode.PR_ONLY,
            min_severity=SeverityThreshold.MEDIUM,
            min_confidence=0.7,
            min_impact_score=50.0,
            max_blast_radius="multi_service",
        )

    @pytest.fixture
    def valid_request(self):
        """Valid remediation request that should pass basic validation."""
        return RemediationRequest(
            incident_id="test-001",
            severity="high",
            confidence=0.8,
            impact_score=70.0,
            blast_radius="single_service",
            affected_files=["src/main.py"],
            rollback_plan="git reset --hard HEAD~1",
            test_plan="pytest tests/",
            rationale="Fix detected issue with configuration",
        )

    @pytest.fixture
    def validator(self, basic_policy):
        """Trust gate validator with test configuration."""
        return TrustGateValidator(policy=basic_policy, environment="test")

    @pytest.mark.asyncio
    async def test_severity_validation_success(self, validator, valid_request):
        """Test successful severity validation."""
        result = ValidationResult(allowed=False)

        success = await validator._validate_severity(valid_request, result)

        assert success is True
        assert result.reason is None
        assert result.message == ""

    @pytest.mark.asyncio
    async def test_severity_validation_failure(self, validator, valid_request):
        """Test severity validation failure."""
        # Set request severity below policy minimum
        low_severity_request = RemediationRequest(
            incident_id="test-002",
            severity="low",  # Below MEDIUM threshold
            confidence=0.8,
            impact_score=70.0,
            blast_radius="single_service",
        )
        result = ValidationResult(allowed=False)

        success = await validator._validate_severity(low_severity_request, result)

        assert success is False
        assert result.reason == DenyReason.SEVERITY_TOO_LOW
        assert "severity 'low' below minimum threshold 'medium'" in result.message
        assert "Escalate to severity >= medium" in result.required_actions

    @pytest.mark.asyncio
    async def test_confidence_validation_success(self, validator, valid_request):
        """Test successful confidence validation."""
        result = ValidationResult(allowed=False)

        success = await validator._validate_confidence(valid_request, result)

        assert success is True
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_confidence_validation_failure(self, validator, valid_request):
        """Test confidence validation failure."""
        low_confidence_request = RemediationRequest(
            incident_id="test-003",
            severity="high",
            confidence=0.5,  # Below 0.7 threshold
            impact_score=70.0,
            blast_radius="single_service",
        )
        result = ValidationResult(allowed=False)

        success = await validator._validate_confidence(low_confidence_request, result)

        assert success is False
        assert result.reason == DenyReason.INSUFFICIENT_CONFIDENCE
        assert "Confidence score 0.5 below minimum threshold 0.7" in result.message

    @pytest.mark.asyncio
    async def test_impact_score_validation_success(self, validator, valid_request):
        """Test successful impact score validation."""
        result = ValidationResult(allowed=False)

        success = await validator._validate_impact_score(valid_request, result)

        assert success is True
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_impact_score_validation_failure(self, validator, valid_request):
        """Test impact score validation failure."""
        low_impact_request = RemediationRequest(
            incident_id="test-004",
            severity="high",
            confidence=0.8,
            impact_score=30.0,  # Below 50.0 threshold
            blast_radius="single_service",
        )
        result = ValidationResult(allowed=False)

        success = await validator._validate_impact_score(low_impact_request, result)

        assert success is False
        assert result.reason == DenyReason.BLOCKED_BY_POLICY
        assert "Impact score 30.0 below minimum threshold 50.0" in result.message

    @pytest.mark.asyncio
    async def test_blast_radius_validation_success(self, validator, valid_request):
        """Test successful blast radius validation."""
        result = ValidationResult(allowed=False)

        success = await validator._validate_blast_radius(valid_request, result)

        assert success is True
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_blast_radius_validation_failure(self, validator, valid_request):
        """Test blast radius validation failure."""
        wide_blast_request = RemediationRequest(
            incident_id="test-005",
            severity="high",
            confidence=0.8,
            impact_score=70.0,
            blast_radius="env_wide",  # Exceeds multi_service limit
        )
        result = ValidationResult(allowed=False)

        success = await validator._validate_blast_radius(wide_blast_request, result)

        assert success is False
        assert result.reason == DenyReason.BLOCKED_BY_POLICY
        assert "exceeds maximum allowed 'multi_service'" in result.message

    @pytest.mark.asyncio
    async def test_protected_paths_validation_deny(self, validator):
        """Test protected path validation with deny action."""
        protected_request = RemediationRequest(
            incident_id="test-006",
            severity="high",
            confidence=0.8,
            impact_score=70.0,
            blast_radius="single_service",
            affected_files=["/etc/kubernetes/admin.conf"],  # Protected system file
        )
        result = ValidationResult(allowed=False)

        success = await validator._validate_protected_paths(protected_request, result)

        assert success is False
        assert result.reason == DenyReason.PROTECTED_PATH
        assert "/etc/kubernetes/admin.conf" in result.message
        assert "matches protected path pattern" in result.message

    @pytest.mark.asyncio
    async def test_protected_paths_validation_require_manual(self, validator):
        """Test protected path validation with require_manual action."""
        # Change policy to non-suggest mode to trigger failure
        validator.policy.mode = PolicyMode.PR_ONLY

        production_request = RemediationRequest(
            incident_id="test-007",
            severity="high",
            confidence=0.8,
            impact_score=70.0,
            blast_radius="single_service",
            affected_files=["apps/production/deployment.yaml"],  # Production file
        )
        result = ValidationResult(allowed=False)

        success = await validator._validate_protected_paths(production_request, result)

        assert success is False
        assert result.reason == DenyReason.PROTECTED_PATH
        assert "requires manual approval" in result.message

    @pytest.mark.asyncio
    async def test_protected_paths_validation_safe_files(self, validator, valid_request):
        """Test protected path validation with safe files."""
        result = ValidationResult(allowed=False)

        success = await validator._validate_protected_paths(valid_request, result)

        assert success is True  # src/main.py should be safe
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_rollback_plan_validation_required(self, validator):
        """Test rollback plan requirement enforcement."""
        validator.policy.require_rollback_plan = True

        no_rollback_request = RemediationRequest(
            incident_id="test-008",
            severity="high",
            confidence=0.8,
            impact_score=70.0,
            blast_radius="single_service",
            rollback_plan=None,  # Missing rollback plan
        )
        result = ValidationResult(allowed=False)

        success = await validator._validate_rollback_plan(no_rollback_request, result)

        assert success is False
        assert result.reason == DenyReason.MISSING_EVIDENCE
        assert "Rollback plan is required but not provided" in result.message

    @pytest.mark.asyncio
    async def test_rollback_plan_validation_not_required(self, validator, valid_request):
        """Test rollback plan when not required."""
        validator.policy.require_rollback_plan = False

        # Remove rollback plan but should still pass
        valid_request.rollback_plan = None
        result = ValidationResult(allowed=False)

        success = await validator._validate_rollback_plan(valid_request, result)

        assert success is True
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_test_plan_validation_required(self, validator):
        """Test test plan requirement enforcement."""
        validator.policy.require_test_plan = True

        no_test_plan_request = RemediationRequest(
            incident_id="test-009",
            severity="high",
            confidence=0.8,
            impact_score=70.0,
            blast_radius="single_service",
            test_plan=None,  # Missing test plan
        )
        result = ValidationResult(allowed=False)

        success = await validator._validate_test_plan(no_test_plan_request, result)

        assert success is False
        assert result.reason == DenyReason.MISSING_EVIDENCE
        assert "Test plan is required but not provided" in result.message


class TestTrustGateValidatorChecks:
    """Test validation check execution and handling."""

    @pytest.fixture
    def validator_with_checks(self):
        """Validator configured with all checks enabled."""
        policy = create_custom_policy(
            mode=PolicyMode.GUARDED_APPLY,
            min_severity=SeverityThreshold.LOW,
        )
        return TrustGateValidator(policy=policy, environment="test")

    @pytest.fixture
    def minimal_request(self):
        """Minimal valid request for check testing."""
        return RemediationRequest(
            incident_id="check-test",
            severity="medium",
            confidence=0.8,
            impact_score=60.0,
            blast_radius="single_service",
            affected_files=["src/app.py"],
            rollback_plan="git reset HEAD~1",
            test_plan="pytest",
        )

    @pytest.mark.asyncio
    async def test_execute_required_checks_all_pass(self, validator_with_checks, minimal_request):
        """Test required checks execution when all checks pass."""
        result = ValidationResult(allowed=False)

        # Mock all checks to pass
        with (
            patch.object(validator_with_checks, "_run_security_scan", return_value=True),
            patch.object(validator_with_checks, "_run_syntax_check", return_value=True),
            patch.object(validator_with_checks, "_run_tests", return_value=True),
        ):
            success = await validator_with_checks._execute_required_checks(minimal_request, result)

            assert success is True
            assert len(result.checks_passed) == 3
            assert len(result.checks_failed) == 0
            assert "tests" in result.checks_passed
            assert "security_scan" in result.checks_passed
            assert "syntax_check" in result.checks_passed

    @pytest.mark.asyncio
    async def test_execute_required_checks_some_fail(self, validator_with_checks, minimal_request):
        """Test required checks execution when some checks fail."""
        result = ValidationResult(allowed=False)

        # Mock security scan to fail, others pass
        with (
            patch.object(validator_with_checks, "_run_security_scan", return_value=False),
            patch.object(validator_with_checks, "_run_syntax_check", return_value=True),
            patch.object(validator_with_checks, "_run_tests", return_value=True),
        ):
            success = await validator_with_checks._execute_required_checks(minimal_request, result)

            assert success is False
            assert result.reason == DenyReason.CHECKS_FAILED
            assert "security_scan" in result.checks_failed
            assert "Required checks failed: security_scan" in result.message
            assert len(result.checks_passed) == 2
            assert len(result.checks_failed) == 1

    @pytest.mark.asyncio
    async def test_security_scan_execution(self, validator_with_checks):
        """Test security scan subprocess execution."""
        # Mock successful bandit execution
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0  # Success
            mock_process.communicate.return_value = (b"[]", b"")
            mock_subprocess.return_value = mock_process

            result = await validator_with_checks._run_security_scan()

            assert result is True
            mock_subprocess.assert_called_once_with(
                "bandit",
                "-r",
                "src/",
                "-f",
                "json",
                "--quiet",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

    @pytest.mark.asyncio
    async def test_security_scan_failure(self, validator_with_checks):
        """Test security scan handling of failures."""
        # Mock failed bandit execution
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1  # Issues found
            mock_process.communicate.return_value = (b'[{"issue": "hardcoded_password"}]', b"")
            mock_subprocess.return_value = mock_process

            result = await validator_with_checks._run_security_scan()

            assert result is False

    @pytest.mark.asyncio
    async def test_security_scan_tool_missing(self, validator_with_checks):
        """Test security scan when bandit is not installed."""
        # Mock FileNotFoundError (tool missing)
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await validator_with_checks._run_security_scan()

            # Should not fail if tool is missing (graceful degradation)
            assert result is True

    @pytest.mark.asyncio
    async def test_syntax_check_python_files(self, validator_with_checks):
        """Test syntax checking of Python files."""
        files = ["src/main.py", "tests/test_app.py"]

        # Mock successful compilation
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0  # Success
            mock_subprocess.return_value = mock_process

            result = await validator_with_checks._run_syntax_check(files)

            assert result is True
            # Should be called once per Python file
            assert mock_subprocess.call_count == 2

    @pytest.mark.asyncio
    async def test_syntax_check_non_python_files(self, validator_with_checks):
        """Test syntax checking skips non-Python files."""
        files = ["README.md", "config.yaml", "script.sh"]

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            result = await validator_with_checks._run_syntax_check(files)

            # Should pass without calling subprocess (no Python files)
            assert result is True
            mock_subprocess.assert_not_called()

    @pytest.mark.asyncio
    async def test_syntax_check_failure(self, validator_with_checks):
        """Test syntax check handling compile errors."""
        files = ["src/broken.py"]

        # Mock compilation failure
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1  # Syntax error
            mock_subprocess.return_value = mock_process

            result = await validator_with_checks._run_syntax_check(files)

            assert result is False

    @pytest.mark.asyncio
    async def test_run_tests_execution(self, validator_with_checks):
        """Test test suite execution."""
        # Mock successful test run
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0  # Tests pass
            mock_process.communicate.return_value = (b"tests passed", b"")
            mock_subprocess.return_value = mock_process

            result = await validator_with_checks._run_tests()

            assert result is True
            mock_subprocess.assert_called_once_with(
                "python",
                "-m",
                "pytest",
                "tests/integration/",  # Updated to match the new directory
                "-x",
                "--tb=no",
                "-q",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

    @pytest.mark.asyncio
    async def test_run_tests_failure(self, validator_with_checks):
        """Test test execution handling test failures."""
        # Mock test failure
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1  # Tests failed
            mock_process.communicate.return_value = (b"FAILED test_app.py", b"")
            mock_subprocess.return_value = mock_process

            result = await validator_with_checks._run_tests()

            assert result is False

    @pytest.mark.asyncio
    async def test_check_execution_with_timeout_handling(self, validator_with_checks, minimal_request):
        """Test check execution timeout handling."""
        result = ValidationResult(allowed=False)

        # Mock check to timeout
        with patch.object(validator_with_checks, "_run_security_scan", side_effect=asyncio.TimeoutError):
            success = await validator_with_checks._execute_required_checks(minimal_request, result)

            assert success is False
            assert result.reason == DenyReason.CHECKS_FAILED
            assert "security_scan" in result.checks_failed


class TestTrustGateValidatorIntegration:
    """Test complete validation flows and integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_validation_success_flow(self):
        """Test complete successful validation from start to finish."""
        policy = create_custom_policy(
            mode=PolicyMode.GUARDED_APPLY,
            min_severity=SeverityThreshold.MEDIUM,
            min_confidence=0.7,
        )
        validator = TrustGateValidator(policy=policy, environment="test")

        request = RemediationRequest(
            incident_id="integration-test",
            severity="high",
            confidence=0.85,
            impact_score=75.0,
            blast_radius="single_service",
            affected_files=["src/service.py"],
            rollback_plan="git revert HEAD",
            test_plan="pytest tests/",
            rationale="Fix critical bug in service logic",
        )

        # Mock all checks to pass
        with (
            patch.object(validator, "_run_security_scan", return_value=True),
            patch.object(validator, "_run_syntax_check", return_value=True),
            patch.object(validator, "_run_tests", return_value=True),
        ):
            result = await validator.validate_remediation(request)

            assert result.allowed is True
            assert result.policy_mode == PolicyMode.GUARDED_APPLY
            assert result.confidence_used == 0.85
            assert len(result.checks_passed) == 3
            assert len(result.checks_failed) == 0
            assert "Remediation approved for guarded execution" in result.message

    @pytest.mark.asyncio
    async def test_policy_summary_and_updates(self):
        """Test policy summary and runtime updates."""
        validator = TrustGateValidator(environment="test")

        # Get initial summary
        summary = validator.get_policy_summary()

        assert "mode" in summary
        assert "min_severity" in summary
        assert "environment" in summary
        assert summary["environment"] == "test"

        # Update policy
        new_policy = create_custom_policy(mode=PolicyMode.PR_ONLY)
        validator.update_policy(new_policy)

        # Verify update
        updated_summary = validator.get_policy_summary()
        assert updated_summary["mode"] == "pr_only"

    def test_get_approval_message_generation(self):
        """Test approval message generation for different modes."""
        validator = TrustGateValidator(environment="test")

        request = RemediationRequest(
            incident_id="msg-test",
            severity="high",
            confidence=0.8,
            impact_score=70.0,
            blast_radius="single_service",
        )

        # Test different policy modes
        validator.policy.mode = PolicyMode.SUGGEST_ONLY
        message = validator._get_approval_message(request)
        assert "approved for suggestion only" in message
        assert "msg-test" in message

        validator.policy.mode = PolicyMode.PR_ONLY
        message = validator._get_approval_message(request)
        assert "approved for PR creation" in message

        validator.policy.mode = PolicyMode.GUARDED_APPLY
        message = validator._get_approval_message(request)
        assert "approved for guarded execution" in message
