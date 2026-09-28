# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Trust Gate policy configuration dataclasses and enums.

Defines the three execution modes (``suggest_only``, ``pr_only``,
``guarded_apply``) and the safety rule structures that the Trust Gate
evaluates before any remediation is applied or submitted as a PR.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


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
    GUARDRAIL_VIOLATION = "guardrail_violation"  # P4: Sovereign Architectural Guardrails


@dataclass
class RequiredCheck:
    """Defines a validation check that must pass before execution."""

    name: str
    description: str
    enabled: bool = True
    timeout_seconds: int = 300


_SUPPORTED_REQUIRED_CHECKS = frozenset({"tests", "security_scan", "syntax_check"})


@dataclass
class ProtectedPathRule:
    """Defines paths that require special handling or are forbidden."""

    pattern: str
    description: str
    action: str  # "deny", "require_manual", "require_approval"
    severity_override: Optional[SeverityThreshold] = None
mutants_xǁPolicyConfigǁvalidate_required_checks__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPolicyConfigǁis_path_protected__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPolicyConfigǁget_required_checks__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPolicyConfigǁvalidate_severity__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPolicyConfigǁvalidate_confidence__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPolicyConfigǁvalidate_impact_score__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut: MutantDict = {}  # type: ignore


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
            RequiredCheck("security_scan", "Security linting with Ruff security rules"),
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

    def __post_init__(self) -> None:
        self.validate_required_checks()

    @_mutmut_mutated(mutants_xǁPolicyConfigǁvalidate_required_checks__mutmut)
    def validate_required_checks(self) -> None:
        """Reject required checks that the Trust Gate cannot execute."""
        unknown = sorted({check.name for check in self.required_checks} - _SUPPORTED_REQUIRED_CHECKS)
        if unknown:
            raise ValueError(f"Unknown required check(s): {', '.join(unknown)}")

    def xǁPolicyConfigǁvalidate_required_checks__mutmut_orig(self) -> None:
        """Reject required checks that the Trust Gate cannot execute."""
        unknown = sorted({check.name for check in self.required_checks} - _SUPPORTED_REQUIRED_CHECKS)
        if unknown:
            raise ValueError(f"Unknown required check(s): {', '.join(unknown)}")

    def xǁPolicyConfigǁvalidate_required_checks__mutmut_1(self) -> None:
        """Reject required checks that the Trust Gate cannot execute."""
        unknown = None
        if unknown:
            raise ValueError(f"Unknown required check(s): {', '.join(unknown)}")

    def xǁPolicyConfigǁvalidate_required_checks__mutmut_2(self) -> None:
        """Reject required checks that the Trust Gate cannot execute."""
        unknown = sorted(None)
        if unknown:
            raise ValueError(f"Unknown required check(s): {', '.join(unknown)}")

    def xǁPolicyConfigǁvalidate_required_checks__mutmut_3(self) -> None:
        """Reject required checks that the Trust Gate cannot execute."""
        unknown = sorted({check.name for check in self.required_checks} + _SUPPORTED_REQUIRED_CHECKS)
        if unknown:
            raise ValueError(f"Unknown required check(s): {', '.join(unknown)}")

    def xǁPolicyConfigǁvalidate_required_checks__mutmut_4(self) -> None:
        """Reject required checks that the Trust Gate cannot execute."""
        unknown = sorted({check.name for check in self.required_checks} - _SUPPORTED_REQUIRED_CHECKS)
        if unknown:
            raise ValueError(None)

    def xǁPolicyConfigǁvalidate_required_checks__mutmut_5(self) -> None:
        """Reject required checks that the Trust Gate cannot execute."""
        unknown = sorted({check.name for check in self.required_checks} - _SUPPORTED_REQUIRED_CHECKS)
        if unknown:
            raise ValueError(f"Unknown required check(s): {', '.join(None)}")

    def xǁPolicyConfigǁvalidate_required_checks__mutmut_6(self) -> None:
        """Reject required checks that the Trust Gate cannot execute."""
        unknown = sorted({check.name for check in self.required_checks} - _SUPPORTED_REQUIRED_CHECKS)
        if unknown:
            raise ValueError(f"Unknown required check(s): {'XX, XX'.join(unknown)}")

    @_mutmut_mutated(mutants_xǁPolicyConfigǁis_path_protected__mutmut)
    def is_path_protected(self, file_path: str) -> tuple[bool, Optional[ProtectedPathRule]]:
        """Check if a file path matches any protected path rules."""
        import fnmatch

        for rule in self.protected_paths:
            if fnmatch.fnmatch(file_path, rule.pattern):
                return True, rule
        return False, None

    def xǁPolicyConfigǁis_path_protected__mutmut_orig(self, file_path: str) -> tuple[bool, Optional[ProtectedPathRule]]:
        """Check if a file path matches any protected path rules."""
        import fnmatch

        for rule in self.protected_paths:
            if fnmatch.fnmatch(file_path, rule.pattern):
                return True, rule
        return False, None

    def xǁPolicyConfigǁis_path_protected__mutmut_1(self, file_path: str) -> tuple[bool, Optional[ProtectedPathRule]]:
        """Check if a file path matches any protected path rules."""
        import fnmatch

        for rule in self.protected_paths:
            if fnmatch.fnmatch(None, rule.pattern):
                return True, rule
        return False, None

    def xǁPolicyConfigǁis_path_protected__mutmut_2(self, file_path: str) -> tuple[bool, Optional[ProtectedPathRule]]:
        """Check if a file path matches any protected path rules."""
        import fnmatch

        for rule in self.protected_paths:
            if fnmatch.fnmatch(file_path, None):
                return True, rule
        return False, None

    def xǁPolicyConfigǁis_path_protected__mutmut_3(self, file_path: str) -> tuple[bool, Optional[ProtectedPathRule]]:
        """Check if a file path matches any protected path rules."""
        import fnmatch

        for rule in self.protected_paths:
            if fnmatch.fnmatch(rule.pattern):
                return True, rule
        return False, None

    def xǁPolicyConfigǁis_path_protected__mutmut_4(self, file_path: str) -> tuple[bool, Optional[ProtectedPathRule]]:
        """Check if a file path matches any protected path rules."""
        import fnmatch

        for rule in self.protected_paths:
            if fnmatch.fnmatch(file_path, ):
                return True, rule
        return False, None

    def xǁPolicyConfigǁis_path_protected__mutmut_5(self, file_path: str) -> tuple[bool, Optional[ProtectedPathRule]]:
        """Check if a file path matches any protected path rules."""
        import fnmatch

        for rule in self.protected_paths:
            if fnmatch.fnmatch(file_path, rule.pattern):
                return False, rule
        return False, None

    def xǁPolicyConfigǁis_path_protected__mutmut_6(self, file_path: str) -> tuple[bool, Optional[ProtectedPathRule]]:
        """Check if a file path matches any protected path rules."""
        import fnmatch

        for rule in self.protected_paths:
            if fnmatch.fnmatch(file_path, rule.pattern):
                return True, rule
        return True, None

    @_mutmut_mutated(mutants_xǁPolicyConfigǁget_required_checks__mutmut)
    def get_required_checks(self, enabled_only: bool = True) -> List[RequiredCheck]:
        """Get list of validation checks, optionally filtered to enabled only."""
        if enabled_only:
            return [check for check in self.required_checks if check.enabled]
        return self.required_checks

    def xǁPolicyConfigǁget_required_checks__mutmut_orig(self, enabled_only: bool = True) -> List[RequiredCheck]:
        """Get list of validation checks, optionally filtered to enabled only."""
        if enabled_only:
            return [check for check in self.required_checks if check.enabled]
        return self.required_checks

    def xǁPolicyConfigǁget_required_checks__mutmut_1(self, enabled_only: bool = False) -> List[RequiredCheck]:
        """Get list of validation checks, optionally filtered to enabled only."""
        if enabled_only:
            return [check for check in self.required_checks if check.enabled]
        return self.required_checks

    @_mutmut_mutated(mutants_xǁPolicyConfigǁvalidate_severity__mutmut)
    def validate_severity(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_orig(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_1(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = None
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_2(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["XXlowXX", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_3(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["LOW", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_4(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "XXmediumXX", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_5(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "MEDIUM", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_6(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "XXhighXX", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_7(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "HIGH", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_8(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "XXcriticalXX"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_9(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "CRITICAL"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_10(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = None
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_11(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(None)
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_12(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = severity_order.rindex(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_13(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.upper())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_14(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = None
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_15(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(None)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_16(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.rindex(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_17(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level > required_level
        except (ValueError, AttributeError):
            return False

    def xǁPolicyConfigǁvalidate_severity__mutmut_18(self, severity: str) -> bool:
        """Check if incident severity meets minimum threshold."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            incident_level = severity_order.index(severity.lower())
            required_level = severity_order.index(self.min_severity.value)
            return incident_level >= required_level
        except (ValueError, AttributeError):
            return True

    @_mutmut_mutated(mutants_xǁPolicyConfigǁvalidate_confidence__mutmut)
    def validate_confidence(self, confidence: float) -> bool:
        """Check if confidence score meets minimum threshold."""
        return confidence >= self.min_confidence

    def xǁPolicyConfigǁvalidate_confidence__mutmut_orig(self, confidence: float) -> bool:
        """Check if confidence score meets minimum threshold."""
        return confidence >= self.min_confidence

    def xǁPolicyConfigǁvalidate_confidence__mutmut_1(self, confidence: float) -> bool:
        """Check if confidence score meets minimum threshold."""
        return confidence > self.min_confidence

    @_mutmut_mutated(mutants_xǁPolicyConfigǁvalidate_impact_score__mutmut)
    def validate_impact_score(self, impact_score: float) -> bool:
        """Check if impact score meets minimum threshold."""
        return impact_score >= self.min_impact_score

    def xǁPolicyConfigǁvalidate_impact_score__mutmut_orig(self, impact_score: float) -> bool:
        """Check if impact score meets minimum threshold."""
        return impact_score >= self.min_impact_score

    def xǁPolicyConfigǁvalidate_impact_score__mutmut_1(self, impact_score: float) -> bool:
        """Check if impact score meets minimum threshold."""
        return impact_score > self.min_impact_score

    @_mutmut_mutated(mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut)
    def validate_blast_radius(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_orig(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_1(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = None
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_2(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["XXsingle_serviceXX", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_3(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["SINGLE_SERVICE", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_4(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "XXmulti_serviceXX", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_5(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "MULTI_SERVICE", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_6(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "XXenv_wideXX"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_7(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "ENV_WIDE"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_8(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "env_wide"]
        try:
            incident_radius = None
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_9(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.index(None)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_10(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.rindex(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_11(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = None
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_12(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(None)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_13(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.rindex(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_14(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius < max_radius
        except ValueError:
            return False

    def xǁPolicyConfigǁvalidate_blast_radius__mutmut_15(self, blast_radius: str) -> bool:
        """Check if blast radius is within acceptable limits."""
        radius_order = ["single_service", "multi_service", "env_wide"]
        try:
            incident_radius = radius_order.index(blast_radius)
            max_radius = radius_order.index(self.max_blast_radius)
            return incident_radius <= max_radius
        except ValueError:
            return True

mutants_xǁPolicyConfigǁvalidate_required_checks__mutmut['_mutmut_orig'] = PolicyConfig.xǁPolicyConfigǁvalidate_required_checks__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_required_checks__mutmut['xǁPolicyConfigǁvalidate_required_checks__mutmut_1'] = PolicyConfig.xǁPolicyConfigǁvalidate_required_checks__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_required_checks__mutmut['xǁPolicyConfigǁvalidate_required_checks__mutmut_2'] = PolicyConfig.xǁPolicyConfigǁvalidate_required_checks__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_required_checks__mutmut['xǁPolicyConfigǁvalidate_required_checks__mutmut_3'] = PolicyConfig.xǁPolicyConfigǁvalidate_required_checks__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_required_checks__mutmut['xǁPolicyConfigǁvalidate_required_checks__mutmut_4'] = PolicyConfig.xǁPolicyConfigǁvalidate_required_checks__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_required_checks__mutmut['xǁPolicyConfigǁvalidate_required_checks__mutmut_5'] = PolicyConfig.xǁPolicyConfigǁvalidate_required_checks__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_required_checks__mutmut['xǁPolicyConfigǁvalidate_required_checks__mutmut_6'] = PolicyConfig.xǁPolicyConfigǁvalidate_required_checks__mutmut_6 # type: ignore # mutmut generated

mutants_xǁPolicyConfigǁis_path_protected__mutmut['_mutmut_orig'] = PolicyConfig.xǁPolicyConfigǁis_path_protected__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁis_path_protected__mutmut['xǁPolicyConfigǁis_path_protected__mutmut_1'] = PolicyConfig.xǁPolicyConfigǁis_path_protected__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁis_path_protected__mutmut['xǁPolicyConfigǁis_path_protected__mutmut_2'] = PolicyConfig.xǁPolicyConfigǁis_path_protected__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁis_path_protected__mutmut['xǁPolicyConfigǁis_path_protected__mutmut_3'] = PolicyConfig.xǁPolicyConfigǁis_path_protected__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁis_path_protected__mutmut['xǁPolicyConfigǁis_path_protected__mutmut_4'] = PolicyConfig.xǁPolicyConfigǁis_path_protected__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁis_path_protected__mutmut['xǁPolicyConfigǁis_path_protected__mutmut_5'] = PolicyConfig.xǁPolicyConfigǁis_path_protected__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁis_path_protected__mutmut['xǁPolicyConfigǁis_path_protected__mutmut_6'] = PolicyConfig.xǁPolicyConfigǁis_path_protected__mutmut_6 # type: ignore # mutmut generated

mutants_xǁPolicyConfigǁget_required_checks__mutmut['_mutmut_orig'] = PolicyConfig.xǁPolicyConfigǁget_required_checks__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁget_required_checks__mutmut['xǁPolicyConfigǁget_required_checks__mutmut_1'] = PolicyConfig.xǁPolicyConfigǁget_required_checks__mutmut_1 # type: ignore # mutmut generated

mutants_xǁPolicyConfigǁvalidate_severity__mutmut['_mutmut_orig'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_1'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_2'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_3'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_4'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_5'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_6'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_7'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_8'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_9'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_10'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_11'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_12'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_12 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_13'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_13 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_14'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_14 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_15'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_15 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_16'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_16 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_17'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_17 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_severity__mutmut['xǁPolicyConfigǁvalidate_severity__mutmut_18'] = PolicyConfig.xǁPolicyConfigǁvalidate_severity__mutmut_18 # type: ignore # mutmut generated

mutants_xǁPolicyConfigǁvalidate_confidence__mutmut['_mutmut_orig'] = PolicyConfig.xǁPolicyConfigǁvalidate_confidence__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_confidence__mutmut['xǁPolicyConfigǁvalidate_confidence__mutmut_1'] = PolicyConfig.xǁPolicyConfigǁvalidate_confidence__mutmut_1 # type: ignore # mutmut generated

mutants_xǁPolicyConfigǁvalidate_impact_score__mutmut['_mutmut_orig'] = PolicyConfig.xǁPolicyConfigǁvalidate_impact_score__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_impact_score__mutmut['xǁPolicyConfigǁvalidate_impact_score__mutmut_1'] = PolicyConfig.xǁPolicyConfigǁvalidate_impact_score__mutmut_1 # type: ignore # mutmut generated

mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['_mutmut_orig'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_1'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_2'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_3'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_4'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_5'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_6'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_7'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_8'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_9'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_10'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_11'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_12'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_12 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_13'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_13 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_14'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_14 # type: ignore # mutmut generated
mutants_xǁPolicyConfigǁvalidate_blast_radius__mutmut['xǁPolicyConfigǁvalidate_blast_radius__mutmut_15'] = PolicyConfig.xǁPolicyConfigǁvalidate_blast_radius__mutmut_15 # type: ignore # mutmut generated


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
mutants_x_load_policy_config__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_load_policy_config__mutmut)
def load_policy_config(environment: str = "production") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return deepcopy(DEFAULT_POLICIES.get(environment, DEFAULT_POLICIES["production"]))


def x_load_policy_config__mutmut_orig(environment: str = "production") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return deepcopy(DEFAULT_POLICIES.get(environment, DEFAULT_POLICIES["production"]))


def x_load_policy_config__mutmut_1(environment: str = "XXproductionXX") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return deepcopy(DEFAULT_POLICIES.get(environment, DEFAULT_POLICIES["production"]))


def x_load_policy_config__mutmut_2(environment: str = "PRODUCTION") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return deepcopy(DEFAULT_POLICIES.get(environment, DEFAULT_POLICIES["production"]))


def x_load_policy_config__mutmut_3(environment: str = "production") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return deepcopy(None)


def x_load_policy_config__mutmut_4(environment: str = "production") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return copy(DEFAULT_POLICIES.get(environment, DEFAULT_POLICIES["production"]))


def x_load_policy_config__mutmut_5(environment: str = "production") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return deepcopy(DEFAULT_POLICIES.get(None, DEFAULT_POLICIES["production"]))


def x_load_policy_config__mutmut_6(environment: str = "production") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return deepcopy(DEFAULT_POLICIES.get(environment, None))


def x_load_policy_config__mutmut_7(environment: str = "production") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return deepcopy(DEFAULT_POLICIES.get(DEFAULT_POLICIES["production"]))


def x_load_policy_config__mutmut_8(environment: str = "production") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return deepcopy(DEFAULT_POLICIES.get(environment, ))


def x_load_policy_config__mutmut_9(environment: str = "production") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return deepcopy(DEFAULT_POLICIES.get(environment, DEFAULT_POLICIES["XXproductionXX"]))


def x_load_policy_config__mutmut_10(environment: str = "production") -> PolicyConfig:
    """Load policy configuration for specified environment."""
    return deepcopy(DEFAULT_POLICIES.get(environment, DEFAULT_POLICIES["PRODUCTION"]))

mutants_x_load_policy_config__mutmut['_mutmut_orig'] = x_load_policy_config__mutmut_orig # type: ignore # mutmut generated
mutants_x_load_policy_config__mutmut['x_load_policy_config__mutmut_1'] = x_load_policy_config__mutmut_1 # type: ignore # mutmut generated
mutants_x_load_policy_config__mutmut['x_load_policy_config__mutmut_2'] = x_load_policy_config__mutmut_2 # type: ignore # mutmut generated
mutants_x_load_policy_config__mutmut['x_load_policy_config__mutmut_3'] = x_load_policy_config__mutmut_3 # type: ignore # mutmut generated
mutants_x_load_policy_config__mutmut['x_load_policy_config__mutmut_4'] = x_load_policy_config__mutmut_4 # type: ignore # mutmut generated
mutants_x_load_policy_config__mutmut['x_load_policy_config__mutmut_5'] = x_load_policy_config__mutmut_5 # type: ignore # mutmut generated
mutants_x_load_policy_config__mutmut['x_load_policy_config__mutmut_6'] = x_load_policy_config__mutmut_6 # type: ignore # mutmut generated
mutants_x_load_policy_config__mutmut['x_load_policy_config__mutmut_7'] = x_load_policy_config__mutmut_7 # type: ignore # mutmut generated
mutants_x_load_policy_config__mutmut['x_load_policy_config__mutmut_8'] = x_load_policy_config__mutmut_8 # type: ignore # mutmut generated
mutants_x_load_policy_config__mutmut['x_load_policy_config__mutmut_9'] = x_load_policy_config__mutmut_9 # type: ignore # mutmut generated
mutants_x_load_policy_config__mutmut['x_load_policy_config__mutmut_10'] = x_load_policy_config__mutmut_10 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_create_custom_policy__mutmut)
def create_custom_policy(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, key):
            setattr(base_policy, key, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_orig(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, key):
            setattr(base_policy, key, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_1(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = None

    for key, value in overrides.items():
        if hasattr(base_policy, key):
            setattr(base_policy, key, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_2(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(None, key):
            setattr(base_policy, key, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_3(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, None):
            setattr(base_policy, key, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_4(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(key):
            setattr(base_policy, key, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_5(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, ):
            setattr(base_policy, key, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_6(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, key):
            setattr(None, key, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_7(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, key):
            setattr(base_policy, None, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_8(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, key):
            setattr(base_policy, key, None)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_9(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, key):
            setattr(key, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_10(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, key):
            setattr(base_policy, value)
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_11(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, key):
            setattr(base_policy, key, )
        else:
            raise ValueError(f"Invalid policy configuration key: {key}")

    base_policy.validate_required_checks()
    return base_policy


def x_create_custom_policy__mutmut_12(**overrides: Any) -> PolicyConfig:
    """Create a custom policy configuration with specified overrides."""
    base_policy = PolicyConfig()

    for key, value in overrides.items():
        if hasattr(base_policy, key):
            setattr(base_policy, key, value)
        else:
            raise ValueError(None)

    base_policy.validate_required_checks()
    return base_policy

mutants_x_create_custom_policy__mutmut['_mutmut_orig'] = x_create_custom_policy__mutmut_orig # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_1'] = x_create_custom_policy__mutmut_1 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_2'] = x_create_custom_policy__mutmut_2 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_3'] = x_create_custom_policy__mutmut_3 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_4'] = x_create_custom_policy__mutmut_4 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_5'] = x_create_custom_policy__mutmut_5 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_6'] = x_create_custom_policy__mutmut_6 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_7'] = x_create_custom_policy__mutmut_7 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_8'] = x_create_custom_policy__mutmut_8 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_9'] = x_create_custom_policy__mutmut_9 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_10'] = x_create_custom_policy__mutmut_10 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_11'] = x_create_custom_policy__mutmut_11 # type: ignore # mutmut generated
mutants_x_create_custom_policy__mutmut['x_create_custom_policy__mutmut_12'] = x_create_custom_policy__mutmut_12 # type: ignore # mutmut generated
