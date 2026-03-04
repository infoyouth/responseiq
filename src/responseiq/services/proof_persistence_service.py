"""
ProofBundle Persistence Service — v2.18.0 #2.

Writes a sealed ``ProofBundle``'s forensic integrity fields to the
``ProofBundleRecord`` SQLite/Postgres table immediately after
``seal_forensic_evidence()`` completes.

SOC2 Rationale
--------------
* Evidence must survive process restarts (in-memory ProofBundle is lost on
  deploy).
* The record is append-only — there is no ``update`` path — so it acts as an
  immutable audit log.
* ``GET /api/v1/incidents/{id}/proof`` lets auditors retrieve cryptographic
  proof hashes without access to the live process.

Trust Gate
----------
rationale    : Closes the SOC2 gap identified in persona review — ProofBundle
               had no durable storage.  This adds a write path with no mutation
               of existing records.
blast_radius : One new DB table (ProofBundleRecord); zero changes to Incident
               or Log tables.
rollback_plan: ``DROP TABLE proofbundlerecord;`` — or simply stop calling
               ``persist_proof_bundle()`` from remediation_service.
"""

from __future__ import annotations

from typing import Optional

from sqlmodel import Session, select

from responseiq.db import get_session
from responseiq.models.base import ProofBundleRecord
from responseiq.schemas.proof import ProofBundle
from responseiq.utils.logger import logger


async def persist_proof_bundle(
    incident_id: str,
    proof_bundle: ProofBundle,
) -> Optional[ProofBundleRecord]:
    """Write a sealed ProofBundle's integrity fields to the DB.

    Args:
        incident_id: String incident identifier (matches
                     ``RemediationRecommendation.incident_id``).
        proof_bundle: A fully sealed ``ProofBundle`` (i.e.
                      ``seal_forensic_evidence()`` has been called).

    Returns:
        The persisted ``ProofBundleRecord`` row, or ``None`` if the bundle
        has no integrity hash (not yet sealed) — in that case a warning is
        logged and no write occurs.

    Note:
        Silently swallows DB errors so a persistence failure can never block
        the remediation response to the caller.  Errors are logged as
        warnings for alerting.
    """
    integrity = proof_bundle.integrity
    if integrity is None or not integrity.integrity_hash:
        logger.warning(
            "⚠️  proof_persistence: ProofBundle has no integrity_hash — "
            "skipping DB persist (not yet sealed?)",
            incident_id=incident_id,
        )
        return None

    record = ProofBundleRecord(
        incident_id=incident_id,
        integrity_hash=integrity.integrity_hash,
        chain_hash=integrity.chain_hash,
        algorithm=integrity.algorithm,
        sealed_at=integrity.sealed_at,
        pre_fix_hash=integrity.pre_fix_hash,
        post_fix_hash=integrity.post_fix_hash,
        chain_verified=integrity.chain_verified,
        tamper_proof=integrity.tamper_proof,
        reproduction_confidence=proof_bundle.reproduction_confidence,
        fix_confidence=proof_bundle.fix_confidence,
    )

    try:
        with next(get_session()) as session:  # type: ignore[call-arg]
            session.add(record)
            session.commit()
            session.refresh(record)
        logger.info(
            "🔐 ProofBundle persisted to DB",
            incident_id=incident_id,
            integrity_hash=str(integrity.integrity_hash)[:16] + "...",
            chain_verified=integrity.chain_verified,
        )
        return record
    except Exception as exc:
        logger.warning(
            "⚠️  proof_persistence: DB write failed — evidence NOT persisted",
            incident_id=incident_id,
            error=str(exc),
        )
        return None


def get_proof_record(incident_id: str, session: Session) -> Optional[ProofBundleRecord]:
    """Retrieve the most-recent ProofBundleRecord for an incident.

    Returns the latest (highest ``id``) record for the given ``incident_id``,
    or ``None`` if no record exists.
    """
    statement = (
        select(ProofBundleRecord)
        .where(ProofBundleRecord.incident_id == incident_id)
        .order_by(ProofBundleRecord.id.desc())  # type: ignore[union-attr]
    )
    results = session.exec(statement).first()
    return results
