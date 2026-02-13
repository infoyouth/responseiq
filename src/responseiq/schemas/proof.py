"""
Proof-oriented evidence schemas for P2 implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ReproductionStatus(Enum):
    """Status of reproduction test execution."""

    NOT_RUN = "not_run"
    FAILED_AS_EXPECTED = "failed_as_expected"
    PASSED_UNEXPECTEDLY = "passed_unexpectedly"
    EXECUTION_ERROR = "execution_error"


class ValidationEvidence(Enum):
    """Types of validation evidence for remediation."""

    PRE_FIX_FAILURE = "pre_fix_failure"
    POST_FIX_SUCCESS = "post_fix_success"
    SECURITY_SCAN = "security_scan"
    TYPE_CHECK = "type_check"
    INTEGRATION_TEST = "integration_test"


@dataclass
class ReproductionTest:
    """
    A generated pytest that reproduces the target incident.

    Follows the principle: Smallest possible code that triggers the bug.
    """

    test_id: str
    test_path: str  # Path relative to tests/repro/
    incident_signature: str  # Expected error pattern to match
    environment_type: str  # "filesystem", "network", "permission", "resource", "version"

    # Test execution state
    status: ReproductionStatus = ReproductionStatus.NOT_RUN
    execution_output: Optional[str] = None
    execution_time: Optional[datetime] = None

    # Test metadata
    description: str = ""
    rationale: str = ""  # Why this reproduction approach was chosen
    mock_dependencies: List[str] = field(default_factory=list)


@dataclass
class ProofBundle:
    """
    Evidence package for a remediation recommendation.

    Core P2 deliverable - replaces "trust me" with deterministic proof.
    """

    incident_id: str
    created_at: datetime

    # Reproduction evidence
    reproduction_test: Optional[ReproductionTest] = None
    pre_fix_evidence: Optional[str] = None  # Test output showing failure
    post_fix_evidence: Optional[str] = None  # Test output showing success

    # Validation evidence
    validation_results: Dict[ValidationEvidence, Any] = field(default_factory=dict)
    security_scan_output: Optional[str] = None
    type_check_output: Optional[str] = None

    # Confidence and trust scores
    reproduction_confidence: float = 0.0  # How well reproduction matches incident
    fix_confidence: float = 0.0  # How confident we are fix works
    missing_evidence: List[ValidationEvidence] = field(default_factory=list)

    @property
    def has_complete_proof(self) -> bool:
        """True if we have both pre-fix failure and post-fix success evidence."""
        return (
            self.reproduction_test is not None
            and self.pre_fix_evidence is not None
            and self.post_fix_evidence is not None
            and len(self.missing_evidence) == 0
        )

    @property
    def blocks_guarded_apply(self) -> bool:
        """True if missing proof should block guarded_apply mode."""
        critical_evidence = {ValidationEvidence.PRE_FIX_FAILURE, ValidationEvidence.POST_FIX_SUCCESS}
        return bool(critical_evidence.intersection(self.missing_evidence))
