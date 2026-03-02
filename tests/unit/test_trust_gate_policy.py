"""
Unit tests for Trust Gate policy configuration and validation logic.
Tests P1 roadmap components: policy modes, rules, and validation.
"""

from dataclasses import replace

import pytest

from responseiq.config.policy_config import (
    DEFAULT_POLICIES,
    DenyReason,
    PolicyConfig,
    PolicyMode,
    ProtectedPathRule,
    RequiredCheck,
    SeverityThreshold,
    create_custom_policy,
    load_policy_config,
)


class TestPolicyConfigValidation:
    """Test core policy configuration validation logic."""

    def test_severity_validation_ordering(self):
        """Test severity threshold validation respects ordering."""
        policy = PolicyConfig(min_severity=SeverityThreshold.HIGH)

        # Above threshold
        assert policy.validate_severity("critical") is True
        assert policy.validate_severity("high") is True

        # Below threshold
        assert policy.validate_severity("medium") is False
        assert policy.validate_severity("low") is False

        # Edge cases
        assert policy.validate_severity("") is False
        assert policy.validate_severity(None) is False
        assert policy.validate_severity("invalid") is False

    def test_confidence_validation_boundaries(self):
        """Test confidence validation with boundary conditions."""
        policy = PolicyConfig(min_confidence=0.7)

        # Valid ranges
        assert policy.validate_confidence(1.0) is True
        assert policy.validate_confidence(0.7) is True  # Exact threshold
        assert policy.validate_confidence(0.75) is True

        # Invalid ranges
        assert policy.validate_confidence(0.69) is False
        assert policy.validate_confidence(0.0) is False
        assert policy.validate_confidence(-0.1) is False

    def test_impact_score_validation(self):
        """Test impact score threshold validation."""
        policy = PolicyConfig(min_impact_score=50.0)

        assert policy.validate_impact_score(100.0) is True
        assert policy.validate_impact_score(50.0) is True  # Exact threshold
        assert policy.validate_impact_score(49.9) is False
        assert policy.validate_impact_score(0.0) is False

    def test_blast_radius_validation_ordering(self):
        """Test blast radius validation respects service scope ordering."""
        policy = PolicyConfig(max_blast_radius="multi_service")

        # Within limits
        assert policy.validate_blast_radius("single_service") is True
        assert policy.validate_blast_radius("multi_service") is True

        # Exceeds limits
        assert policy.validate_blast_radius("env_wide") is False

        # Invalid values
        assert policy.validate_blast_radius("invalid") is False
        assert policy.validate_blast_radius("") is False

    def test_protected_path_pattern_matching(self):
        """Test protected path rule pattern matching."""
        policy = PolicyConfig()

        # System configuration files
        is_protected, rule = policy.is_path_protected("/etc/kubernetes/admin.conf")
        assert is_protected
        assert rule.pattern == "/etc/*"
        assert rule.action == "deny"

        # Production environment files
        is_protected, rule = policy.is_path_protected("apps/production/deployment.yaml")
        assert is_protected
        assert rule.pattern == "*/production/*"
        assert rule.action == "require_manual"

        # Database files
        is_protected, rule = policy.is_path_protected("migrations/schema.sql")
        assert is_protected
        assert rule.pattern == "*.sql"
        assert rule.action == "require_approval"

        # Secrets
        is_protected, rule = policy.is_path_protected("config/secrets/api-key.yaml")
        assert is_protected
        assert rule.pattern == "**/secrets/**"
        assert rule.action == "deny"

        # Safe paths
        is_protected, rule = policy.is_path_protected("src/main.py")
        assert not is_protected
        assert rule is None

    def test_required_checks_filtering(self):
        """Test filtering of required checks by enabled status."""
        checks = [
            RequiredCheck("tests", "Run tests", enabled=True),
            RequiredCheck("security_scan", "Security scan", enabled=False),
            RequiredCheck("syntax_check", "Syntax validation", enabled=True),
        ]
        policy = PolicyConfig(required_checks=checks)

        # Get enabled only
        enabled_checks = policy.get_required_checks(enabled_only=True)
        assert len(enabled_checks) == 2
        assert all(check.enabled for check in enabled_checks)
        assert {check.name for check in enabled_checks} == {"tests", "syntax_check"}

        # Get all checks
        all_checks = policy.get_required_checks(enabled_only=False)
        assert len(all_checks) == 3
        assert "security_scan" in {check.name for check in all_checks}


class TestPolicyModeConfiguration:
    """Test policy mode enum and behavior."""

    def test_policy_mode_values(self):
        """Test policy mode enum values."""
        assert PolicyMode.SUGGEST_ONLY.value == "suggest_only"
        assert PolicyMode.PR_ONLY.value == "pr_only"
        assert PolicyMode.GUARDED_APPLY.value == "guarded_apply"

    def test_severity_threshold_values(self):
        """Test severity threshold enum values."""
        assert SeverityThreshold.LOW.value == "low"
        assert SeverityThreshold.MEDIUM.value == "medium"
        assert SeverityThreshold.HIGH.value == "high"
        assert SeverityThreshold.CRITICAL.value == "critical"

    def test_deny_reason_values(self):
        """Test deny reason enum completeness."""
        expected_reasons = {
            "blocked_by_policy",
            "checks_failed",
            "missing_evidence",
            "protected_path",
            "severity_too_low",
            "insufficient_confidence",
            "guardrail_violation",  # P4: Sovereign Architectural Guardrails
        }
        actual_reasons = {reason.value for reason in DenyReason}
        assert actual_reasons == expected_reasons


class TestProtectedPathRules:
    """Test protected path rule configuration and matching."""

    def test_protected_path_rule_creation(self):
        """Test protected path rule dataclass creation."""
        rule = ProtectedPathRule(
            pattern="*/sensitive/*",
            description="Sensitive files require approval",
            action="require_approval",
            severity_override=SeverityThreshold.CRITICAL,
        )

        assert rule.pattern == "*/sensitive/*"
        assert rule.description == "Sensitive files require approval"
        assert rule.action == "require_approval"
        assert rule.severity_override == SeverityThreshold.CRITICAL

    def test_default_protected_paths_coverage(self):
        """Test default protected paths cover security-critical patterns."""
        policy = PolicyConfig()

        # Should protect system config
        assert policy.is_path_protected("/etc/passwd")[0]
        assert policy.is_path_protected("/etc/kubernetes/config")[0]

        # Should protect production
        assert policy.is_path_protected("k8s/production/secrets.yaml")[0]
        assert policy.is_path_protected("helm/production/values.yaml")[0]

        # Should protect SQL files
        assert policy.is_path_protected("db/migration.sql")[0]
        assert policy.is_path_protected("scripts/cleanup.sql")[0]

        # Should protect secrets
        assert policy.is_path_protected("config/secrets/token.yaml")[0]
        assert policy.is_path_protected("k8s/app/secrets/db-password.yaml")[0]

    def test_different_protection_actions(self):
        """Test different protection action types."""
        rules = [
            ProtectedPathRule("*/deny/*", "Deny access", "deny"),
            ProtectedPathRule("*/manual/*", "Manual required", "require_manual"),
            ProtectedPathRule("*/approve/*", "Approval required", "require_approval"),
        ]
        policy = PolicyConfig(protected_paths=rules)

        # Test deny action
        is_protected, rule = policy.is_path_protected("app/deny/config.yaml")
        assert is_protected and rule.action == "deny"

        # Test manual action
        is_protected, rule = policy.is_path_protected("app/manual/config.yaml")
        assert is_protected and rule.action == "require_manual"

        # Test approval action
        is_protected, rule = policy.is_path_protected("app/approve/config.yaml")
        assert is_protected and rule.action == "require_approval"


class TestRequiredChecks:
    """Test required check configuration and properties."""

    def test_required_check_creation(self):
        """Test required check dataclass creation."""
        check = RequiredCheck(
            name="custom_lint", description="Custom linting rules", enabled=False, timeout_seconds=600
        )

        assert check.name == "custom_lint"
        assert check.description == "Custom linting rules"
        assert check.enabled is False
        assert check.timeout_seconds == 600

    def test_required_check_defaults(self):
        """Test required check default values."""
        check = RequiredCheck("basic_test", "Basic test suite")

        assert check.enabled is True  # Default enabled
        assert check.timeout_seconds == 300  # Default timeout

    def test_default_required_checks(self):
        """Test default required checks are comprehensive."""
        policy = PolicyConfig()
        default_checks = {check.name for check in policy.required_checks}

        # Should include security, testing, and syntax validation
        expected_checks = {"tests", "security_scan", "syntax_check"}
        assert default_checks == expected_checks

        # All should be enabled by default
        assert all(check.enabled for check in policy.required_checks)


class TestPolicyConfigDefaults:
    """Test default policy configurations for different environments."""

    def test_default_environment_policies_exist(self):
        """Test default policies exist for expected environments."""
        assert "development" in DEFAULT_POLICIES
        assert "staging" in DEFAULT_POLICIES
        assert "production" in DEFAULT_POLICIES

    def test_development_policy_permissive(self):
        """Test development policy is appropriately permissive."""
        dev_policy = DEFAULT_POLICIES["development"]

        assert dev_policy.mode == PolicyMode.GUARDED_APPLY
        assert dev_policy.min_severity == SeverityThreshold.LOW
        assert dev_policy.min_confidence == 0.5
        assert dev_policy.min_impact_score == 20.0
        assert dev_policy.require_rollback_plan is False
        assert dev_policy.require_test_plan is False

    def test_staging_policy_balanced(self):
        """Test staging policy balances safety and automation."""
        staging_policy = DEFAULT_POLICIES["staging"]

        assert staging_policy.mode == PolicyMode.PR_ONLY
        assert staging_policy.min_severity == SeverityThreshold.MEDIUM
        assert staging_policy.min_confidence == 0.6
        assert staging_policy.min_impact_score == 40.0
        assert staging_policy.require_rollback_plan is True
        assert staging_policy.require_test_plan is True

    def test_production_policy_strict(self):
        """Test production policy is maximally strict."""
        prod_policy = DEFAULT_POLICIES["production"]

        assert prod_policy.mode == PolicyMode.SUGGEST_ONLY
        assert prod_policy.min_severity == SeverityThreshold.HIGH
        assert prod_policy.min_confidence == 0.8
        assert prod_policy.min_impact_score == 70.0
        assert prod_policy.max_blast_radius == "single_service"
        assert prod_policy.require_rollback_plan is True
        assert prod_policy.require_test_plan is True

    def test_load_policy_config_function(self):
        """Test policy loading function."""
        # Load known environment
        prod_policy = load_policy_config("production")
        assert prod_policy.mode == PolicyMode.SUGGEST_ONLY

        # Load unknown environment defaults to production
        unknown_policy = load_policy_config("nonexistent")
        assert unknown_policy.mode == PolicyMode.SUGGEST_ONLY
        assert unknown_policy.min_severity == SeverityThreshold.HIGH


class TestCustomPolicyCreation:
    """Test custom policy creation and validation."""

    def test_create_custom_policy_with_overrides(self):
        """Test creating custom policy with specific overrides."""
        custom_policy = create_custom_policy(
            mode=PolicyMode.PR_ONLY, min_confidence=0.9, max_blast_radius="single_service", require_rollback_plan=False
        )

        # Overridden values
        assert custom_policy.mode == PolicyMode.PR_ONLY
        assert custom_policy.min_confidence == 0.9
        assert custom_policy.max_blast_radius == "single_service"
        assert custom_policy.require_rollback_plan is False

        # Default values preserved
        assert custom_policy.min_severity == SeverityThreshold.MEDIUM
        assert custom_policy.min_impact_score == 50.0

    def test_custom_policy_invalid_attribute(self):
        """Test custom policy creation rejects invalid attributes."""
        with pytest.raises(ValueError, match="Invalid policy configuration key"):
            create_custom_policy(invalid_attribute="value")

    def test_custom_policy_preserves_structure(self):
        """Test custom policy preserves all expected attributes."""
        custom_policy = create_custom_policy(mode=PolicyMode.PR_ONLY)
        base_policy = PolicyConfig()

        # Should have same attribute structure
        assert set(dir(custom_policy)) == set(dir(base_policy))

        # Should preserve method functionality
        assert hasattr(custom_policy, "validate_severity")
        assert hasattr(custom_policy, "is_path_protected")
        assert hasattr(custom_policy, "get_required_checks")


class TestPolicyConfigIntegration:
    """Test policy configuration integration scenarios."""

    def test_policy_config_immutability_pattern(self):
        """Test policy config can be safely copied and modified."""
        original_policy = PolicyConfig()

        # Create modified copy
        modified_policy = replace(original_policy, mode=PolicyMode.GUARDED_APPLY, min_confidence=0.9)

        # Original should be unchanged
        assert original_policy.mode == PolicyMode.SUGGEST_ONLY
        assert original_policy.min_confidence == 0.7

        # Modified should have new values
        assert modified_policy.mode == PolicyMode.GUARDED_APPLY
        assert modified_policy.min_confidence == 0.9

    def test_policy_version_tracking(self):
        """Test policy version and metadata tracking."""
        policy = PolicyConfig()

        assert policy.policy_version == "1.0"
        assert policy.last_updated is None  # Not set by default

        # Custom policy with metadata
        custom_policy = PolicyConfig(policy_version="2.1", last_updated="2026-02-12T10:00:00Z")

        assert custom_policy.policy_version == "2.1"
        assert custom_policy.last_updated == "2026-02-12T10:00:00Z"

    def test_complete_policy_validation_scenario(self):
        """Test realistic scenario with multiple validation checks."""
        # Create enterprise-like policy
        enterprise_policy = create_custom_policy(
            mode=PolicyMode.PR_ONLY,
            min_severity=SeverityThreshold.HIGH,
            min_confidence=0.85,
            min_impact_score=75.0,
            max_blast_radius="single_service",
            require_rollback_plan=True,
            require_test_plan=True,
        )

        # Test high-quality incident (should pass)
        assert enterprise_policy.validate_severity("critical")
        assert enterprise_policy.validate_confidence(0.9)
        assert enterprise_policy.validate_impact_score(80.0)
        assert enterprise_policy.validate_blast_radius("single_service")

        # Test marginal incident (should fail multiple checks)
        assert not enterprise_policy.validate_severity("medium")
        assert not enterprise_policy.validate_confidence(0.7)
        assert not enterprise_policy.validate_impact_score(60.0)
        assert not enterprise_policy.validate_blast_radius("env_wide")
