"""tests/unit/test_integrity_gate.py

P2 Integrity Gate closure — unit tests.

Coverage:
- ProofBundle.seal_forensic_evidence() now ASSIGNS the returned sealed object
  (previous bug: seal_evidence return value was discarded)
- integrity_hash and chain_hash are populated after sealing
- chain_verified=True when both pre and post evidence present
- Re-sealing with post_fix_evidence updates the hashes
- proof_integrity dict exported from RemediationRecommendation.to_dict()
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from hypothesis import HealthCheck, given, settings as hypothesis_settings, strategies as st

from responseiq.schemas.proof import EvidenceIntegrity, EvidenceLevel, ProofBundle, ReproductionTest, ValidationEvidence


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _bundle(**kwargs) -> ProofBundle:
    return ProofBundle(incident_id="test-123", created_at=datetime.now(timezone.utc), **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# seal_forensic_evidence assignment fix
# ─────────────────────────────────────────────────────────────────────────────


class TestSealForensicEvidence:
    def test_production_observation_requires_time_and_traffic_thresholds(self):
        bundle = _bundle(reproduction_test=ReproductionTest("test", "test.py", "Error", "filesystem"))
        bundle.validation_results[ValidationEvidence.PRODUCTION_OBSERVED] = {"passed": True}
        bundle.production_elapsed_seconds = 1799
        bundle.production_request_volume = 100
        bundle.production_request_baseline = 100
        assert bundle.evidence_level == EvidenceLevel.SYNTHETIC_SIGNATURE

        bundle.production_elapsed_seconds = 1800
        bundle.production_request_volume = 99
        assert bundle.evidence_level == EvidenceLevel.SYNTHETIC_SIGNATURE

        bundle.production_request_volume = 100
        assert bundle.evidence_level == EvidenceLevel.PRODUCTION_OBSERVED

    def test_canonical_payload_is_sealed_and_verifiable(self):
        bundle = _bundle(
            pre_fix_evidence="pre: failure",
            post_fix_evidence="post: success",
            security_scan_output="ruff clean",
        )
        bundle.validation_results = {"tests": {"passed": True}}
        bundle.seal_forensic_evidence()

        assert bundle.integrity.payload_json == bundle.canonical_payload_json()
        assert bundle.integrity.previous_hash is None
        assert bundle.verify_evidence_integrity() is True

        bundle.security_scan_output = "tampered"
        assert bundle.verify_evidence_integrity() is False

    def test_reseal_links_to_previous_chain_hash(self):
        bundle = _bundle(pre_fix_evidence="pre: failure")
        bundle.seal_forensic_evidence()
        first_chain_hash = bundle.integrity.chain_hash

        bundle.post_fix_evidence = "post: success"
        bundle.seal_forensic_evidence()

        assert bundle.integrity.previous_hash == first_chain_hash
        assert bundle.integrity.chain_hash != first_chain_hash
        assert bundle.verify_evidence_integrity() is True

    def test_integrity_hash_populated_after_seal(self):
        """After sealing, ProofBundle.integrity.integrity_hash must be non-None."""
        bundle = _bundle(pre_fix_evidence="test failed: AssertionError at line 42")
        bundle.seal_forensic_evidence()

        assert bundle.integrity is not None
        assert bundle.integrity.integrity_hash is not None
        assert len(bundle.integrity.integrity_hash) == 64  # SHA-256 hex

    def test_chain_hash_populated_after_seal(self):
        bundle = _bundle(pre_fix_evidence="FAIL: ImportError")
        bundle.seal_forensic_evidence()
        assert bundle.integrity.chain_hash is not None

    def test_seal_with_only_pre_fix(self):
        bundle = _bundle(pre_fix_evidence="pre_fix output")
        bundle.seal_forensic_evidence()
        assert bundle.integrity.pre_fix_hash is not None
        assert bundle.integrity.post_fix_hash is None
        assert bundle.integrity.chain_verified is False  # missing post_fix

    def test_seal_with_both_pre_and_post(self):
        bundle = _bundle(
            pre_fix_evidence="pre: FAILED",
            post_fix_evidence='{"checks_passed": ["syntax"], "allowed": true}',
        )
        bundle.seal_forensic_evidence()
        assert bundle.integrity.pre_fix_hash is not None
        assert bundle.integrity.post_fix_hash is not None
        assert bundle.integrity.chain_verified is True
        assert bundle.integrity.tamper_proof is True

    def test_reseal_updates_chain_when_post_fix_added(self):
        """Re-sealing after adding post_fix_evidence sets post_fix_hash + chain_verified."""
        bundle = _bundle(pre_fix_evidence="pre: FAILED")
        bundle.seal_forensic_evidence()
        assert bundle.integrity.post_fix_hash is None
        assert bundle.integrity.chain_verified is False

        bundle.post_fix_evidence = '{"checks_passed": ["tests"], "allowed": true}'
        bundle.seal_forensic_evidence()

        assert bundle.integrity.post_fix_hash is not None
        assert bundle.integrity.chain_verified is True
        assert bundle.integrity.tamper_proof is True

    def test_sealed_at_is_set(self):
        bundle = _bundle(pre_fix_evidence="pre output")
        bundle.seal_forensic_evidence()
        assert bundle.integrity.sealed_at is not None

    def test_algorithm_is_sha256(self):
        bundle = _bundle(pre_fix_evidence="data")
        bundle.seal_forensic_evidence()
        assert bundle.integrity.algorithm == "SHA-256"

    def test_no_pre_fix_evidence_still_seals(self):
        """No evidence → integrity_hash derived from empty string, still non-None."""
        bundle = _bundle()
        bundle.seal_forensic_evidence()
        assert bundle.integrity is not None
        assert bundle.integrity.integrity_hash is not None

    def test_verify_evidence_integrity_passes_after_seal(self):
        """verify_evidence_integrity() must return True for un-tampered evidence."""
        bundle = _bundle(
            pre_fix_evidence="pre: error",
            post_fix_evidence="post: ok",
        )
        bundle.seal_forensic_evidence()
        assert bundle.verify_evidence_integrity() is True

    def test_tamper_detection(self):
        """Modifying evidence after sealing must break verify_evidence_integrity()."""
        bundle = _bundle(pre_fix_evidence="original pre evidence")
        bundle.seal_forensic_evidence()

        bundle.pre_fix_evidence = "MODIFIED — tampered"
        assert bundle.verify_evidence_integrity() is False


# ─────────────────────────────────────────────────────────────────────────────
# EvidenceIntegrity.seal_evidence returns a new object each time
# ─────────────────────────────────────────────────────────────────────────────


class TestEvidenceIntegritySealing:
    @pytest.mark.property
    @hypothesis_settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.differing_executors],
    )
    @given(pre_fix=st.text(min_size=1, max_size=200), post_fix=st.text(min_size=1, max_size=200))
    def test_arbitrary_evidence_round_trips_and_rejects_tampering(self, pre_fix, post_fix):
        sealed = EvidenceIntegrity().seal_evidence(pre_fix_content=pre_fix, post_fix_content=post_fix)

        assert sealed.verify_pre_fix_evidence(pre_fix)
        assert sealed.verify_post_fix_evidence(post_fix)
        assert sealed.chain_verified is True
        assert sealed.verify_pre_fix_evidence(f"{pre_fix}tampered") is False
        assert sealed.verify_post_fix_evidence(f"{post_fix}tampered") is False

    def test_seal_returns_new_instance(self):
        ei = EvidenceIntegrity()
        sealed = ei.seal_evidence(pre_fix_content="data")
        assert sealed is not ei  # must be a new object

    def test_repeated_seals_are_deterministic(self):
        ei = EvidenceIntegrity()
        s1 = ei.seal_evidence(pre_fix_content="same data")
        s2 = ei.seal_evidence(pre_fix_content="same data")
        assert s1.integrity_hash == s2.integrity_hash

    def test_different_content_different_hash(self):
        ei = EvidenceIntegrity()
        s1 = ei.seal_evidence(pre_fix_content="data A")
        s2 = ei.seal_evidence(pre_fix_content="data B")
        assert s1.integrity_hash != s2.integrity_hash

    def test_chain_hash_incorporates_previous(self):
        ei = EvidenceIntegrity()
        s1 = ei.seal_evidence(pre_fix_content="data")
        s2 = ei.seal_evidence(pre_fix_content="data", previous_hash=s1.chain_hash)
        assert s1.chain_hash != s2.chain_hash
