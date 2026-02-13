"""
Proof-oriented evidence schemas for P2 implementation.
"""

from __future__ import annotations

import hashlib
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
class Evidence:
    """
    Basic evidence unit for forensic integrity system.
    Represents any piece of analysis evidence that can be sealed and verified.
    """

    type: str  # Type of evidence (e.g., "shadow_analysis", "fix_result", "reproduction_test")
    content: Dict[str, Any]  # Evidence payload
    source: str  # Source system/service that generated the evidence
    timestamp: datetime  # When the evidence was created
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata


@dataclass
class EvidenceIntegrity:
    """Forensic integrity block for tamper-proof evidence.

    NOTE: This class provides a high-level sealing API that the tests expect
    (seal_evidence returning a sealed-like object and verify_evidence_integrity
    that accepts a sealed object + evidence). To remain backward-compatible the
    instance is returned by `seal_evidence`.
    """

    pre_fix_hash: Optional[str] = None  # SHA-256 of pre-fix test output (hex)
    post_fix_hash: Optional[str] = None  # SHA-256 of post-fix test output (hex)
    evidence_timestamp: Optional[datetime] = None  # When evidence was captured
    tamper_proof: bool = False  # True if at least one hash present
    chain_verified: bool = False  # True if full evidence chain is intact

    # Public sealing metadata (tests expect these attributes on the returned object)
    integrity_hash: Optional[str] = None
    chain_hash: Optional[str] = None
    sealed_at: Optional[datetime] = None
    algorithm: str = "SHA-256"

    @staticmethod
    def _content_to_canonical_str(content: Any) -> str:
        """Canonicalize evidence content to a deterministic string for hashing."""
        import json

        if isinstance(content, str):
            return content
        try:
            return json.dumps(content, sort_keys=True, default=str)
        except Exception:
            return str(content)

    @staticmethod
    def generate_hash(content: str, prefix: bool = False) -> str:
        """Generate SHA-256 hash of content for integrity verification.

        Returns hex digest by default; if prefix=True returns 'sha256:<hex>'.
        """
        h = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return f"sha256:{h}" if prefix else h

    def verify_pre_fix_evidence(self, content: str) -> bool:
        """Verify pre-fix evidence hasn't been tampered with."""
        if not self.pre_fix_hash or not content:
            return False
        return self.pre_fix_hash == self.generate_hash(self._content_to_canonical_str(content))

    def verify_post_fix_evidence(self, content: str) -> bool:
        """Verify post-fix evidence hasn't been tampered with."""
        if not self.post_fix_hash or not content:
            return False
        return self.post_fix_hash == self.generate_hash(self._content_to_canonical_str(content))

    def seal_evidence(
        self,
        evidence: Optional["Evidence"] = None,
        *,
        pre_fix_content: Optional[str] = None,
        post_fix_content: Optional[str] = None,
        previous_hash: Optional[str] = None,
    ) -> "EvidenceIntegrity":
        """Seal evidence and return the sealing object (self).

        Accepts either an `Evidence` object (preferred in e2e tests) or
        pre/post fix content strings. Computes `integrity_hash` (SHA-256 hex), a
        `chain_hash` (sha256(integrity_hash + previous_hash|'')), and stores
        sealing metadata on the instance. Returns `self` so callers can use
        the returned `sealed` object in assertions.
        """
        # Derive contents from Evidence if provided
        if evidence is not None:
            content_str = self._content_to_canonical_str(evidence.content)
            pre_fix_content = pre_fix_content or content_str

        # Canonicalize inputs
        pre_canonical = self._content_to_canonical_str(pre_fix_content) if pre_fix_content else None
        post_canonical = self._content_to_canonical_str(post_fix_content) if post_fix_content else None

        # Compute individual hashes (hex without prefix)
        if pre_canonical:
            self.pre_fix_hash = self.generate_hash(pre_canonical)
        if post_canonical:
            self.post_fix_hash = self.generate_hash(post_canonical)

        # Compute primary integrity hash (prefer pre_fix_hash, else post_fix_hash)
        primary = self.pre_fix_hash or self.post_fix_hash or ""
        self.integrity_hash = primary or self.generate_hash(
            self._content_to_canonical_str(evidence.content) if evidence else ""
        )

        # Chain hash combines integrity + previous (if provided)
        if previous_hash:
            combined = f"{self.integrity_hash}{previous_hash}"
        else:
            combined = f"{self.integrity_hash}"
        self.chain_hash = hashlib.sha256(combined.encode()).hexdigest()

        # Timestamps / metadata
        self.sealed_at = datetime.now()
        self.algorithm = "SHA-256"

        # Flags
        self.tamper_proof = bool(self.pre_fix_hash or self.post_fix_hash)
        self.chain_verified = bool(self.pre_fix_hash and self.post_fix_hash)

        return self

    def verify_evidence_integrity(self, sealed, evidence: "Evidence") -> bool:
        """Verify that `sealed` matches the given `evidence` content.

        This helper is used heavily in tests where callers pass the `sealed`
        object returned from `seal_evidence` and an `Evidence` instance.
        """
        if not sealed or not evidence:
            return False

        expected = self.generate_hash(self._content_to_canonical_str(evidence.content))
        return getattr(sealed, "integrity_hash", None) == expected


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

    # Forensic integrity (P2.1 feature)
    integrity: Optional[EvidenceIntegrity] = field(default_factory=EvidenceIntegrity)

    @property
    def has_complete_proof(self) -> bool:
        """True if we have both pre-fix failure and post-fix success evidence.

        Note: presence of both pre/post fix evidence and no missing evidence is
        considered a complete proof even if the forensic sealing step hasn't
        been executed yet (tests construct ProofBundle objects directly).
        """
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

    def seal_forensic_evidence(self) -> None:
        """Seal evidence with cryptographic hashes for audit trail."""
        if not self.integrity:
            self.integrity = EvidenceIntegrity()

        self.integrity.seal_evidence(self.pre_fix_evidence, self.post_fix_evidence)

    def verify_evidence_integrity(self) -> bool:
        """Verify that evidence hasn't been tampered with since sealing."""
        if not self.integrity:
            return False

        pre_fix_valid = True
        post_fix_valid = True

        if self.pre_fix_evidence:
            pre_fix_valid = self.integrity.verify_pre_fix_evidence(self.pre_fix_evidence)

        if self.post_fix_evidence:
            post_fix_valid = self.integrity.verify_post_fix_evidence(self.post_fix_evidence)

        return pre_fix_valid and post_fix_valid
