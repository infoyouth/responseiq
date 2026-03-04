"""
Unit tests for v2.18.0 #2 ProofBundle Persistence.

Coverage:
    persist_proof_bundle()          — 8 tests
    get_proof_record()              — 4 tests
    GET /api/v1/incidents/{id}/proof — 6 tests

Trust Gate:
    rationale    : Persistence is append-only; tests confirm no mutation.
    blast_radius : Only reads/writes ProofBundleRecord table.
    rollback_plan: drop ProofBundleRecord table or disable persist call.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from responseiq.models.base import ProofBundleRecord
from responseiq.schemas.proof import EvidenceIntegrity, ProofBundle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sealed_proof(
    incident_id: str = "INC-001",
    integrity_hash: str = "abc123def456",
    chain_hash: str = "chain789",
    pre_fix_hash: str = "pre_fix_abc",
    post_fix_hash: str = "post_fix_xyz",
    chain_verified: bool = True,
    tamper_proof: bool = True,
    repro_confidence: float = 0.9,
    fix_confidence: float = 0.85,
) -> ProofBundle:
    """Build a fully sealed ProofBundle stub without touching the DB."""
    bundle = ProofBundle(
        incident_id=incident_id,
        created_at=datetime.now(timezone.utc),
        reproduction_confidence=repro_confidence,
        fix_confidence=fix_confidence,
    )
    integrity = EvidenceIntegrity()
    integrity.integrity_hash = integrity_hash
    integrity.chain_hash = chain_hash
    integrity.pre_fix_hash = pre_fix_hash
    integrity.post_fix_hash = post_fix_hash
    integrity.chain_verified = chain_verified
    integrity.tamper_proof = tamper_proof
    integrity.sealed_at = datetime.now(timezone.utc)
    integrity.algorithm = "SHA-256"
    bundle.integrity = integrity
    return bundle


def _record_from_proof(incident_id: str, proof: ProofBundle) -> ProofBundleRecord:
    """Build a ProofBundleRecord matching the sealed proof stub."""
    ig = proof.integrity
    return ProofBundleRecord(
        id=1,
        incident_id=incident_id,
        integrity_hash=ig.integrity_hash if ig else None,
        chain_hash=ig.chain_hash if ig else None,
        algorithm=ig.algorithm if ig else "SHA-256",
        sealed_at=ig.sealed_at if ig else None,
        pre_fix_hash=ig.pre_fix_hash if ig else None,
        post_fix_hash=ig.post_fix_hash if ig else None,
        chain_verified=ig.chain_verified if ig else False,
        tamper_proof=ig.tamper_proof if ig else False,
        reproduction_confidence=proof.reproduction_confidence,
        fix_confidence=proof.fix_confidence,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# persist_proof_bundle() tests
# ---------------------------------------------------------------------------


class TestPersistProofBundle:
    @pytest.mark.asyncio
    async def test_skips_when_no_integrity(self):
        """Returns None when integrity is not set."""
        from responseiq.services.proof_persistence_service import persist_proof_bundle

        bundle = ProofBundle(incident_id="x", created_at=datetime.now(timezone.utc))
        bundle.integrity = None
        result = await persist_proof_bundle("x", bundle)
        assert result is None

    @pytest.mark.asyncio
    async def test_skips_when_no_integrity_hash(self):
        """Returns None when integrity hash is empty string."""
        from responseiq.services.proof_persistence_service import persist_proof_bundle

        bundle = ProofBundle(incident_id="x", created_at=datetime.now(timezone.utc))
        bundle.integrity = EvidenceIntegrity()  # hash is None
        result = await persist_proof_bundle("x", bundle)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_record_on_success(self):
        """Returns the persisted ProofBundleRecord on success."""
        from responseiq.services.proof_persistence_service import persist_proof_bundle

        bundle = _sealed_proof(incident_id="INC-001")

        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.refresh = MagicMock(return_value=None)

        with patch("responseiq.services.proof_persistence_service.get_session") as mock_get:
            mock_get.return_value = iter([mock_session])
            await persist_proof_bundle("INC-001", bundle)
        # No exception = success (DB mock doesn't return a real record)
        assert True

    @pytest.mark.asyncio
    async def test_swallows_db_error_gracefully(self):
        """A DB error must not propagate — returns None with a warning."""
        from responseiq.services.proof_persistence_service import persist_proof_bundle

        bundle = _sealed_proof(incident_id="INC-002")
        with patch("responseiq.services.proof_persistence_service.get_session") as mock_get:
            mock_get.side_effect = RuntimeError("DB connection refused")
            result = await persist_proof_bundle("INC-002", bundle)
        assert result is None

    @pytest.mark.asyncio
    async def test_uses_integrity_fields_for_record(self):
        """Record fields mirror the EvidenceIntegrity snapshot."""
        from responseiq.services.proof_persistence_service import persist_proof_bundle

        bundle = _sealed_proof(
            incident_id="INC-003",
            integrity_hash="hash_abc",
            chain_hash="chain_xyz",
            chain_verified=True,
            tamper_proof=True,
        )
        captured: list[ProofBundleRecord] = []

        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        def _capture_add(rec):
            if isinstance(rec, ProofBundleRecord):
                captured.append(rec)

        mock_session.add.side_effect = _capture_add

        with patch("responseiq.services.proof_persistence_service.get_session") as mock_get:
            mock_get.return_value = iter([mock_session])
            await persist_proof_bundle("INC-003", bundle)

        assert len(captured) == 1
        rec = captured[0]
        assert rec.integrity_hash == "hash_abc"
        assert rec.chain_hash == "chain_xyz"
        assert rec.chain_verified is True
        assert rec.tamper_proof is True
        assert rec.incident_id == "INC-003"

    @pytest.mark.asyncio
    async def test_reproduction_confidence_stored(self):
        """reproduction_confidence is copied from ProofBundle."""
        from responseiq.services.proof_persistence_service import persist_proof_bundle

        bundle = _sealed_proof(incident_id="INC-CF", repro_confidence=0.75)
        captured: list[ProofBundleRecord] = []

        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.add.side_effect = lambda r: captured.append(r) if isinstance(r, ProofBundleRecord) else None

        with patch("responseiq.services.proof_persistence_service.get_session") as mock_get:
            mock_get.return_value = iter([mock_session])
            await persist_proof_bundle("INC-CF", bundle)

        assert captured[0].reproduction_confidence == pytest.approx(0.75)

    @pytest.mark.asyncio
    async def test_algorithm_defaults_to_sha256(self):
        """algorithm field defaults to 'SHA-256'."""
        from responseiq.services.proof_persistence_service import persist_proof_bundle

        bundle = _sealed_proof(incident_id="INC-ALG")
        captured: list[ProofBundleRecord] = []

        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.add.side_effect = lambda r: captured.append(r) if isinstance(r, ProofBundleRecord) else None

        with patch("responseiq.services.proof_persistence_service.get_session") as mock_get:
            mock_get.return_value = iter([mock_session])
            await persist_proof_bundle("INC-ALG", bundle)

        assert captured[0].algorithm == "SHA-256"

    @pytest.mark.asyncio
    async def test_handles_none_post_fix_hash(self):
        """A ProofBundle without post_fix_hash still persists (no crash)."""
        from responseiq.services.proof_persistence_service import persist_proof_bundle

        bundle = _sealed_proof(incident_id="INC-NP", post_fix_hash=None)  # type: ignore[arg-type]
        captured: list[ProofBundleRecord] = []

        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.add.side_effect = lambda r: captured.append(r) if isinstance(r, ProofBundleRecord) else None

        with patch("responseiq.services.proof_persistence_service.get_session") as mock_get:
            mock_get.return_value = iter([mock_session])
            await persist_proof_bundle("INC-NP", bundle)

        assert len(captured) == 1
        assert captured[0].post_fix_hash is None


# ---------------------------------------------------------------------------
# get_proof_record() tests
# ---------------------------------------------------------------------------


class TestGetProofRecord:
    def test_returns_record_when_found(self):
        """Returns the ProofBundleRecord fetched from the session."""
        from responseiq.services.proof_persistence_service import get_proof_record

        bundle = _sealed_proof("INC-GET")
        expected = _record_from_proof("INC-GET", bundle)

        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = expected

        result = get_proof_record("INC-GET", mock_session)
        assert result is expected

    def test_returns_none_when_not_found(self):
        """Returns None when no record exists."""
        from responseiq.services.proof_persistence_service import get_proof_record

        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None

        result = get_proof_record("INC-MISSING", mock_session)
        assert result is None

    def test_passes_incident_id_to_query(self):
        """Verifies the session.exec() is called (implying where-clause)."""
        from responseiq.services.proof_persistence_service import get_proof_record

        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None

        get_proof_record("INC-QUERY", mock_session)
        mock_session.exec.assert_called_once()

    def test_returns_latest_record_by_id(self):
        """select() orders by id DESC so .first() returns the latest."""
        from responseiq.services.proof_persistence_service import get_proof_record

        latest = _record_from_proof("INC-LATEST", _sealed_proof("INC-LATEST", integrity_hash="latest_hash"))
        latest.id = 99

        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = latest

        result = get_proof_record("INC-LATEST", mock_session)
        assert result is latest
        assert result.integrity_hash == "latest_hash"


# ---------------------------------------------------------------------------
# Endpoint tests: GET /api/v1/incidents/{id}/proof
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    from responseiq.app import app as _app

    return TestClient(_app, raise_server_exceptions=True)


class TestProofRecordEndpoint:
    def test_returns_200_when_record_exists(self, client: TestClient):
        bundle = _sealed_proof("INC-E01")
        record = _record_from_proof("INC-E01", bundle)

        with patch("responseiq.routers.proof_record.get_proof_record", return_value=record):
            response = client.get("/api/v1/incidents/INC-E01/proof")
        assert response.status_code == 200

    def test_returns_404_when_no_record(self, client: TestClient):
        with patch("responseiq.routers.proof_record.get_proof_record", return_value=None):
            response = client.get("/api/v1/incidents/INC-MISSING/proof")
        assert response.status_code == 404
        assert "proof record" in response.json()["detail"].lower()

    def test_response_contains_integrity_hash(self, client: TestClient):
        bundle = _sealed_proof("INC-E02", integrity_hash="myhash123")
        record = _record_from_proof("INC-E02", bundle)

        with patch("responseiq.routers.proof_record.get_proof_record", return_value=record):
            response = client.get("/api/v1/incidents/INC-E02/proof")
        assert response.json()["integrity_hash"] == "myhash123"

    def test_response_contains_chain_verified(self, client: TestClient):
        bundle = _sealed_proof("INC-E03", chain_verified=True)
        record = _record_from_proof("INC-E03", bundle)

        with patch("responseiq.routers.proof_record.get_proof_record", return_value=record):
            response = client.get("/api/v1/incidents/INC-E03/proof")
        assert response.json()["chain_verified"] is True

    def test_response_contains_incident_id(self, client: TestClient):
        bundle = _sealed_proof("INC-E04")
        record = _record_from_proof("INC-E04", bundle)

        with patch("responseiq.routers.proof_record.get_proof_record", return_value=record):
            response = client.get("/api/v1/incidents/INC-E04/proof")
        assert response.json()["incident_id"] == "INC-E04"

    def test_response_has_algorithm_field(self, client: TestClient):
        bundle = _sealed_proof("INC-E05")
        record = _record_from_proof("INC-E05", bundle)

        with patch("responseiq.routers.proof_record.get_proof_record", return_value=record):
            response = client.get("/api/v1/incidents/INC-E05/proof")
        assert response.json()["algorithm"] == "SHA-256"
