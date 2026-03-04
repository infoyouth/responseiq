"""
src/responseiq/routers/causal_graph.py — P6: Causal Root-Cause Graph endpoint

GET /api/v1/incidents/{incident_id}/causal-graph

Fetches incident data from the DB and builds a causal graph on-demand.
No separate storage table needed — graph is derived from existing signals.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from responseiq.db import get_session
from responseiq.models.base import Incident
from responseiq.schemas.causal_graph import CausalGraph
from responseiq.services.causal_graph_service import build_causal_graph
from responseiq.utils.logger import logger

router = APIRouter(prefix="/api/v1/incidents", tags=["causal-graph"])


@router.get("/{incident_id}/causal-graph", response_model=CausalGraph)
def get_causal_graph(
    incident_id: str,
    session: Session = Depends(get_session),
) -> CausalGraph:
    """
    Return the causal root-cause graph for an incident.

    The graph assembles from stored incident metadata — no re-analysis is
    triggered.  Confidence scores degrade gracefully when upstream signal
    (git correlation, perf data) is absent.
    """
    # Incident.id is an integer primary key — only numeric lookups are valid.
    incident_row: Incident | None = None
    if incident_id.isdigit():
        incident_row = session.get(Incident, int(incident_id))

    if incident_row is None:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")

    # Build a minimal analysis dict from the stored incident
    analysis_result = {
        "title": getattr(incident_row, "description", None) or getattr(incident_row, "source", "Unknown error"),
        "severity": getattr(incident_row, "severity", "unknown") or "unknown",
        "description": getattr(incident_row, "description", None),
    }
    impact_score: float = 0.0  # Not stored on Incident; graph degrades gracefully

    logger.info("P6 causal-graph requested", incident_id=incident_id)

    return build_causal_graph(
        incident_id=str(incident_id),
        analysis_result=analysis_result,
        correlation=None,  # Not persisted yet — on-demand build has no P3 data
        impact_score=impact_score,
        perf_result=None,
        proof_bundle=None,
    )
