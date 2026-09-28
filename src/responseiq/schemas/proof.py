# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Proof-oriented evidence schemas for the Trust Gate audit trail.

A ``ProofBundle`` is sealed with SHA-256 after every Trust Gate
decision and stored immutably. ``ReproductionTest`` and
``ValidationEvidence`` carry the supporting artefacts — the failing
pytest script, runtime output, and patch diff.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
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
    PRODUCTION_OBSERVED = "production_observed"


class EvidenceLevel(str, Enum):
    """Strongest validation tier supported by a proof bundle."""

    SYNTHETIC_SIGNATURE = "synthetic_signature"
    STATIC_VALIDATION = "static_validation"
    APPLICATION_REPRODUCTION = "application_reproduction"
    INTEGRATION_VALIDATION = "integration_validation"
    PRODUCTION_OBSERVED = "production_observed"


class ContextResolutionReason(str, Enum):
    """Why context extraction failed for a particular stack-trace reference."""

    REPO_NOT_CONFIGURED = "repo_not_configured"
    LOCAL_NOT_FOUND = "local_not_found"
    REMOTE_CLONE_FAILED = "remote_clone_failed"
    FILE_NOT_FOUND = "file_not_found"
    PARSE_ERROR = "parse_error"


@dataclass
class ContextResolutionFailure:
    """
    Records why a stack-trace file reference could not be resolved.

    Appended to ``ProofBundle.context_failures`` so the downstream
    LLM prompt and audit trail know exactly which frames had no source.
    """

    path: str  # Raw path string from the stack trace
    line_num: int
    reason: ContextResolutionReason
    attempted_repos: List[str] = field(default_factory=list)
    detail: str = ""  # Human-readable extra info (e.g. git error)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "line_num": self.line_num,
            "reason": self.reason.value,
            "attempted_repos": self.attempted_repos,
            "detail": self.detail,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass(frozen=True)
class SourceReference:
    """Resolved source location used to build an LLM context block."""

    path: str
    line_num: int
    scope: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "line_num": self.line_num,
            "scope": self.scope,
        }


@dataclass
class SourceContext:
    """Rendered source context and its resolution provenance."""

    rendered: str = ""
    references: List[SourceReference] = field(default_factory=list)
    failures: List[ContextResolutionFailure] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rendered": self.rendered,
            "references": [reference.to_dict() for reference in self.references],
            "failures": [failure.to_dict() for failure in self.failures],
        }


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
    repro_method: str = "unknown"  # 'llm_synthesis' or 'static_fallback'

    # Forensic Integrity
    test_file_hash: Optional[str] = None  # SHA-256 hash of the generated test file
    execution_log_hash: Optional[str] = None  # SHA-256 hash of the execution output


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
    previous_hash: Optional[str] = None
    payload_json: Optional[str] = None
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
        payload: Any = None,
    ) -> "EvidenceIntegrity":
        """Seal evidence and return the sealing object (self).

        Accepts either an `Evidence` object (preferred in e2e tests) or
        pre/post fix content strings. Computes `integrity_hash` (SHA-256 hex), a
        `chain_hash` (sha256(integrity_hash + previous_hash|'')), and stores
        sealing metadata on the instance. Returns `self` so callers can use
        the returned `sealed` object in assertions.
        """
        # Build a new sealed object so callers receive an immutable snapshot
        # of the sealing operation (tests expect separate sealed instances).
        sealed = EvidenceIntegrity()

        # Derive contents from Evidence if provided
        if evidence is not None:
            content_str = self._content_to_canonical_str(evidence.content)
            pre_fix_content = pre_fix_content or content_str
            payload = evidence.content

        # Canonicalize inputs
        pre_canonical = self._content_to_canonical_str(pre_fix_content) if pre_fix_content else None
        post_canonical = self._content_to_canonical_str(post_fix_content) if post_fix_content else None

        # Compute individual hashes (hex without prefix) on the sealed snapshot
        if pre_canonical:
            sealed.pre_fix_hash = self.generate_hash(pre_canonical)
        if post_canonical:
            sealed.post_fix_hash = self.generate_hash(post_canonical)

        # Deterministic integrity hash: when an Evidence object is supplied,
        # derive integrity_hash directly from its canonicalized content so that
        # different evidence yields different integrity hashes (security test
        # requirement). Otherwise fall back to pre/post hashes.
        if payload is not None:
            payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
            sealed.payload_json = payload_json
            sealed.integrity_hash = self.generate_hash(payload_json)
        else:
            sealed.integrity_hash = sealed.pre_fix_hash or sealed.post_fix_hash or self.generate_hash("")

        # Chain hash combines integrity + previous (if provided)
        sealed.previous_hash = previous_hash
        combined = f"{sealed.integrity_hash}{previous_hash or ''}"
        sealed.chain_hash = hashlib.sha256(combined.encode()).hexdigest()

        # Timestamps / metadata
        sealed.sealed_at = datetime.now()
        sealed.algorithm = "SHA-256"

        # Flags
        sealed.tamper_proof = bool(sealed.pre_fix_hash or sealed.post_fix_hash)
        sealed.chain_verified = bool(sealed.pre_fix_hash and sealed.post_fix_hash)

        return sealed

    def verify_evidence_integrity(self, sealed, evidence: "Evidence") -> bool:
        """Verify that `sealed` matches the given `evidence` content.

        This helper is used heavily in tests where callers pass the `sealed`
        object returned from `seal_evidence` and an `Evidence` instance.
        """
        if not sealed or not evidence:
            return False

        expected = self.generate_hash(
            json.dumps(evidence.content, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
        )
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
    validation_metadata: Dict[str, Any] = field(default_factory=dict)

    # Confidence and trust scores
    reproduction_confidence: float = 0.0  # How well reproduction matches incident
    fix_confidence: float = 0.0  # How confident we are fix works
    missing_evidence: List[ValidationEvidence] = field(default_factory=list)

    # Forensic integrity (P2.1 feature)
    integrity: Optional[EvidenceIntegrity] = field(default_factory=EvidenceIntegrity)

    # Multi-repo context resolution failures (P2.4)
    # Populated when stack-trace paths could not be resolved to source files.
    context_failures: List[ContextResolutionFailure] = field(default_factory=list)
    source_context: Optional[SourceContext] = None

    # P5: Performance regression gate result
    # Populated after gate.evaluate() is called during post-fix verification.
    perf_gate_result: Optional[object] = None  # PerformanceGateResult (avoid circular import)

    production_elapsed_seconds: float = 0.0
    production_request_volume: int = 0
    production_request_baseline: int = 0

    def _validation_passed(self, evidence_type: ValidationEvidence) -> bool:
        result = self.validation_results.get(evidence_type)
        if isinstance(result, dict):
            return result.get("passed") is True
        return result is True

    @property
    def evidence_level(self) -> Optional[EvidenceLevel]:
        """Return the strongest level backed by explicitly successful evidence."""
        if (
            self._validation_passed(ValidationEvidence.PRODUCTION_OBSERVED)
            and self.production_elapsed_seconds >= 1800
            and self.production_request_volume >= self.production_request_baseline
        ):
            return EvidenceLevel.PRODUCTION_OBSERVED
        if self._validation_passed(ValidationEvidence.INTEGRATION_TEST):
            return EvidenceLevel.INTEGRATION_VALIDATION

        has_real_reproduction = (
            self.reproduction_test is not None and self.reproduction_test.repro_method != "static_fallback"
        )
        if (
            has_real_reproduction
            and self._validation_passed(ValidationEvidence.PRE_FIX_FAILURE)
            and self._validation_passed(ValidationEvidence.POST_FIX_SUCCESS)
        ):
            return EvidenceLevel.APPLICATION_REPRODUCTION

        if any(
            self._validation_passed(evidence_type)
            for evidence_type in (ValidationEvidence.SECURITY_SCAN, ValidationEvidence.TYPE_CHECK)
        ):
            return EvidenceLevel.STATIC_VALIDATION

        if self.reproduction_test is not None:
            return EvidenceLevel.SYNTHETIC_SIGNATURE

        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the bundle with its derived evidence level."""
        result = asdict(self)
        result["evidence_level"] = self.evidence_level.value if self.evidence_level else None
        result["source_context"] = self.source_context.to_dict() if self.source_context else None
        return result

    @staticmethod
    def _canonical_value(value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {str(key): ProofBundle._canonical_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [ProofBundle._canonical_value(item) for item in value]
        if hasattr(value, "__dataclass_fields__"):
            return ProofBundle._canonical_value(asdict(value))
        return value

    def canonical_payload(self) -> Dict[str, Any]:
        """Return all proof inputs in a deterministic, integrity-safe shape."""
        return self._canonical_value(
            {
                "incident_id": self.incident_id,
                "created_at": self.created_at,
                "reproduction_test": self.reproduction_test,
                "pre_fix_evidence": self.pre_fix_evidence,
                "post_fix_evidence": self.post_fix_evidence,
                "validation_results": self.validation_results,
                "security_scan_output": self.security_scan_output,
                "type_check_output": self.type_check_output,
                "validation_metadata": self.validation_metadata,
                "reproduction_confidence": self.reproduction_confidence,
                "fix_confidence": self.fix_confidence,
                "missing_evidence": self.missing_evidence,
                "context_failures": self.context_failures,
                "source_context": self.source_context,
                "perf_gate_result": self.perf_gate_result,
                "production_elapsed_seconds": self.production_elapsed_seconds,
                "production_request_volume": self.production_request_volume,
                "production_request_baseline": self.production_request_baseline,
            }
        )

    def canonical_payload_json(self) -> str:
        return json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

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
        # IMPORTANT: seal_evidence() returns a *new* EvidenceIntegrity snapshot.
        # Assign it back so ProofBundle.integrity carries the populated hashes.
        previous_hash = self.integrity.chain_hash
        self.integrity = self.integrity.seal_evidence(
            pre_fix_content=self.pre_fix_evidence,
            post_fix_content=self.post_fix_evidence,
            previous_hash=previous_hash,
            payload=self.canonical_payload(),
        )

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

        payload_valid = self.integrity.payload_json == self.canonical_payload_json()
        chain_valid = self.integrity.chain_hash == EvidenceIntegrity.generate_hash(
            f"{self.integrity.integrity_hash}{self.integrity.previous_hash or ''}"
        )
        return pre_fix_valid and post_fix_valid and payload_valid and chain_valid
