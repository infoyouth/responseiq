"""
Policy Configuration for ResponseIQ Trust Gate v1
Defines execution modes, safety rules, and validation requirements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class PolicyMode(str, Enum):
    """Execution policy modes for remediation actions."""

    SUGGEST_ONLY = "suggest_only"  # Only suggest, never execute
    PR_ONLY = "pr_only"  # Create PR, require manual merge
    GUARDED_APPLY = "guarded_apply"  # Execute after all checks pass


class SeverityThreshold(str, Enum):
    """Minimum severity required for auto-execution."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DenyReason(str, Enum):
    """Standardized denial reasons for policy violations."""

    BLOCKED_BY_POLICY = "blocked_by_policy"
    CHECKS_FAILED = "checks_failed"
    MISSING_EVIDENCE = "missing_evidence"
    PROTECTED_PATH = "protected_path"
    SEVERITY_TOO_LOW = "severity_too_low"
    INSUFFICIENT_CONFIDENCE = "insufficient_confidence"


@dataclass
class RequiredCheck:
    """Defines a validation check that must pass before execution."""

    name: str
    description: str
    enabled: bool = True
    timeout_seconds: int = 300


@dataclass
class ProtectedPathRule:
    """Defines paths that require special handling or are forbidden."""

    pattern: str
    description: str
    action: str  # "deny", "require_manual", "require_approval"
    severity_override: Optional[SeverityThreshold] = None


@dataclass
class PolicyConfig:
    """Complete policy configuration for trust gate validation."""

    # Core execution mode
    mode: PolicyMode = PolicyMode.SUGGEST_ONLY

    # Severity and confidence thresholds
    min_severity: SeverityThreshold = SeverityThreshold.MEDIUM
    min_confidence: float = 0.7
    min_impact_score: float = 50.0

    # Required validation checks
    required_checks: List[RequiredCheck] = field(
        default_factory=lambda: [
            RequiredCheck("tests", "Unit/integration tests must pass"),
            RequiredCheck("security_scan", "Security linting with Bandit"),
            RequiredCheck("syntax_check", "Code syntax validation"),
        ]
    )

    # Protected path rules
    protected_paths: List[ProtectedPathRule] = field(
        default_factory=lambda: [
            ProtectedPathRule(pattern="/etc/*", description="System configuration files", action="deny"),
            ProtectedPathRule(
                pattern="*/production/*",
                description="Production environment files",
                action="require_manual",
                severity_override=SeverityThreshold.CRITICAL,
            ),
            ProtectedPathRule(pattern="*.sql", description="Database migration files", action="require_approval"),
            ProtectedPathRule(pattern="**/secrets/**", description="Secret management files", action="deny"),
        ]
    )

    # Rollback requirements
    require_rollback_plan: bool = True
    require_test_plan: bool = True

    # Blast radius limits
    max_blast_radius: str = "multi_service"  # "single_service", "multi_service", "env_wide"

    # Additional metadata
    policy_version: str = "1.0"
    last_updated: Optional[str] = None

    def is_path_protected(self, file_path: str) -> tuple[bool, Optional[ProtectedPathRule]]:
        """Check if a file path matches any protected path rules."""
        import fnmatch

        for rule in self.protected_paths:
            if fnmatch.fnmatch(file_path, rule.pattern):
                return True, rule
        return False, None

    def get_required_checks(self, enabled_only: bool = True) -> List[RequiredCheck]:
        """Get list of validation checks, optionally filtered to enabled only."""
        if enabled_only:
            return [check for check in self.required_checks if check.enabled]
        return self.required_checks

    def validate_severity(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def validate_confidence(self, confidence: float) -> bool:
        """Check if confidence score meets minimum threshold."""
        return confidence >= self.min_confidence

    def validate_impact_score(self, impact_score: float) -> bool:
        """Check if impact score meets minimum threshold."""
        return impact_score >= self.min_impact_score

    def validate_blast_radius(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False


# Default configurations for different deployment environments
DEFAULT_POLICIES = {
    "development": PolicyConfig(
        mode=PolicyMode.GUARDED_APPLY,
        min_severity=SeverityThreshold.LOW,
        min_confidence=0.5,
        min_impact_score=20.0,
        require_rollback_plan=False,
        require_test_plan=False,
    ),
    "staging": PolicyConfig(
        mode=PolicyMode.PR_ONLY,
        min_severity=SeverityThreshold.MEDIUM,
        min_confidence=0.6,
        min_impact_score=40.0,
    ),
    "production": PolicyConfig(
        mode=PolicyMode.SUGGEST_ONLY,
        min_severity=SeverityThreshold.HIGH,
        min_confidence=0.8,
        min_impact_score=70.0,
        max_blast_radius="single_service",
    ),
}


def load_policy_config(environment: str = "production") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return DEFAULT_POLICIES.get(environment, DEFAULT_POLICIES["production"])


def create_custom_policy(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, key):
            setattr(base_policy, key, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    return base_policy
