"""
ProofBundle Record Router — v2.18.0 #2 SOC2 Audit Endpoint.

GET /api/v1/incidents/{incident_id}/proof

Returns the most-recent sealed ProofBundle record for an incident, enabling
auditors and SOC2 reviewers to verify cryptographic evidence chains without
access to the live process.

Trust Gate
----------
rationale    : Read-only endpoint exposing immutable DB records — zero
               mutation risk.
blast_radius : None — only SELECTs from ProofBundleRecord table.
rollback_plan: Remove router include from app.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from responseiq.db import get_session
from responseiq.services.proof_persistence_service import get_proof_record

router = APIRouter(prefix="/api/v1/incidents", tags=["Proof & Audit"])


@router.get(
    "/{incident_id}/proof",
    summary="Retrieve the sealed ProofBundle audit record for an incident",
    responses={
        200: {"description": "ProofBundle integrity record"},
        404: {"description": "No proof record found for this incident"},
    },
)
def get_incident_proof(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """
    Return the most-recent ``ProofBundleRecord`` for the given incident.

    The record contains:
    - ``integrity_hash``   — SHA-256 of the sealed evidence payload
    - ``chain_hash``       — SHA-256(integrity_hash + previous_hash)
    - ``sealed_at``        — UTC timestamp when sealing occurred
    - ``chain_verified``   — True when both pre- and post-fix hashes present
    - ``tamper_proof``     — True if at least one hash is present
    - ``pre_fix_hash``     — SHA-256 of pre-fix test output
    - ``post_fix_hash``    — SHA-256 of post-fix validation output

    Args:
        incident_id: String incident identifier (uuid or slug).

    Raises:
        HTTPException 404: when no ProofBundleRecord exists for this incident.
    """
    record = get_proof_record(incident_id=incident_id, session=session)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No proof record found for incident '{incident_id}'. "
            "The incident may not have run through the full remediation "
            "pipeline, or proof persistence may not yet be enabled.",
        )
    return {
        "incident_id": record.incident_id,
        "integrity_hash": record.integrity_hash,
        "chain_hash": record.chain_hash,
        "algorithm": record.algorithm,
        "sealed_at": record.sealed_at.isoformat() if record.sealed_at else None,
        "pre_fix_hash": record.pre_fix_hash,
        "post_fix_hash": record.post_fix_hash,
        "chain_verified": record.chain_verified,
        "tamper_proof": record.tamper_proof,
        "reproduction_confidence": record.reproduction_confidence,
        "fix_confidence": record.fix_confidence,
        "created_at": record.created_at.isoformat(),
    }
