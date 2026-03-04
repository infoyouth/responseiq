"""
src/responseiq/services/causal_graph_service.py — P6: Causal Root-Cause Graph

Assembles a machine-readable causal chain from the signals already collected
during a remediation run (P3 Git correlation, P5 performance data, impact
score, AI analysis, P2 proof bundle).

No new I/O is performed — this is a pure transformation step.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from responseiq.schemas.causal_graph import (
    CausalEdge,
    CausalGraph,
    CausalNode,
    EdgeType,
    NodeType,
)
from responseiq.utils.logger import logger


def build_causal_graph(
    incident_id: str,
    analysis_result: Optional[Dict[str, Any]] = None,
    correlation: Optional[Any] = None,  # CorrelationResult | None
    impact_score: float = 0.0,
    perf_result: Optional[Any] = None,  # PerformanceResult | None
    proof_bundle: Optional[Any] = None,  # ProofBundle | None
) -> CausalGraph:
    """
    Build a CausalGraph from remediation-pipeline signals.

    Parameters mirror the data already available in RemediationService after
    the trust-gate pass — no duplicate work required.

    Chain structure
    ---------------
    [deploy_event]  →  [latency_spike]  →  [error_log]  →  [affected_code]
                                                        →  [policy_decision]

    Nodes and edges are omitted when the source signal is unavailable so the
    graph degrades gracefully on minimal data.
    """
    nodes: list[CausalNode] = []
    edges: list[CausalEdge] = []
    edge_confidences: list[float] = []

    # --- Node 1: Deploy Event (from P3 Git correlation) ---
    deploy_node_id: Optional[str] = None
    if correlation and getattr(correlation, "suspect_commit", None):
        deploy_node_id = "deploy_event"
        nodes.append(
            CausalNode(
                id=deploy_node_id,
                type=NodeType.DEPLOY_EVENT,
                label=f"Suspect commit: {correlation.suspect_commit}",
                detail=str(correlation.diff_summary) if correlation.diff_summary else None,
                confidence=float(correlation.confidence_score),
                metadata={
                    "sha": str(correlation.suspect_commit_sha or ""),
                    "files": list(correlation.suspect_files),
                    "method": str(correlation.method),
                },
            )
        )

    # --- Node 2: Latency Spike (from P5 performance gate) ---
    latency_node_id: Optional[str] = None
    if perf_result and getattr(perf_result, "regression_detected", False):
        latency_node_id = "latency_spike"
        delta = getattr(perf_result, "delta_pct", 0.0)
        nodes.append(
            CausalNode(
                id=latency_node_id,
                type=NodeType.LATENCY_SPIKE,
                label=f"Latency regression: +{delta:.1f}%",
                detail=getattr(perf_result, "reason", None),
                confidence=0.9,
                metadata={"delta_pct": delta},
            )
        )
        if deploy_node_id:
            conf = round((correlation.confidence_score + 0.9) / 2, 3)  # type: ignore[union-attr]
            edges.append(
                CausalEdge(
                    source_id=deploy_node_id,
                    target_id=latency_node_id,
                    type=EdgeType.CAUSED,
                    label="deploy caused latency spike",
                    confidence=conf,
                )
            )
            edge_confidences.append(conf)

    # --- Node 3: Error Log (from AI analysis) ---
    error_node_id: Optional[str] = None
    title = (analysis_result or {}).get("title", "")
    severity = (analysis_result or {}).get("severity", "unknown")
    if title:
        error_node_id = "error_log"
        nodes.append(
            CausalNode(
                id=error_node_id,
                type=NodeType.ERROR_LOG,
                label=title,
                detail=(analysis_result or {}).get("description"),
                confidence=min(1.0, impact_score / 100.0) if impact_score else 0.5,
                metadata={
                    "severity": severity,
                    "impact_score": impact_score,
                },
            )
        )
        # Edge from whichever upstream node exists
        upstream = latency_node_id or deploy_node_id
        if upstream:
            conf = round(min(1.0, impact_score / 100.0), 3) if impact_score else 0.5
            edges.append(
                CausalEdge(
                    source_id=upstream,
                    target_id=error_node_id,
                    type=EdgeType.TRIGGERED,
                    label="triggered error condition",
                    confidence=conf,
                )
            )
            edge_confidences.append(conf)

    # --- Node 4: Affected Code Line (from P2 proof bundle) ---
    if proof_bundle and getattr(proof_bundle, "reproduction_test", None):
        repro = proof_bundle.reproduction_test
        affected_node_id = "affected_code"
        nodes.append(
            CausalNode(
                id=affected_node_id,
                type=NodeType.AFFECTED_CODE,
                label=f"Reproduction test: {str(getattr(repro, 'test_path', 'unknown'))}",
                detail=str(getattr(repro, "incident_signature", None) or ""),
                confidence=float(getattr(proof_bundle, "reproduction_confidence", 0.8)),
                metadata={
                    "environment_type": str(getattr(repro, "environment_type", "")),
                    "pre_fix_evidence": bool(proof_bundle.pre_fix_evidence),
                },
            )
        )
        if error_node_id:
            conf = float(getattr(proof_bundle, "reproduction_confidence", 0.8))
            edges.append(
                CausalEdge(
                    source_id=error_node_id,
                    target_id=affected_node_id,
                    type=EdgeType.CORRELATED,
                    label="error reproduced in test",
                    confidence=conf,
                )
            )
            edge_confidences.append(conf)

    # --- Node 5: Policy Decision (always present) ---
    policy_node_id = "policy_decision"
    nodes.append(
        CausalNode(
            id=policy_node_id,
            type=NodeType.POLICY_DECISION,
            label="Trust Gate evaluation",
            detail="ResponseIQ trust-gate policy check",
            confidence=1.0,
            metadata={"incident_id": incident_id},
        )
    )
    upstream_for_policy = error_node_id or latency_node_id or deploy_node_id
    if upstream_for_policy:
        edges.append(
            CausalEdge(
                source_id=upstream_for_policy,
                target_id=policy_node_id,
                type=EdgeType.TRIGGERED,
                label="triggered policy evaluation",
                confidence=1.0,
            )
        )
        edge_confidences.append(1.0)

    # --- Overall confidence = min of all edge confidences ---
    overall_confidence = round(min(edge_confidences), 3) if edge_confidences else 0.0

    # --- Summary narrative ---
    summary_parts: list[str] = []
    if deploy_node_id:
        summary_parts.append(f"Suspect commit '{correlation.suspect_commit}' was identified")  # type: ignore[union-attr]
    if latency_node_id:
        summary_parts.append(f"latency regression of +{getattr(perf_result, 'delta_pct', 0):.1f}% was observed")
    if error_node_id:
        summary_parts.append(f"error '{title}' (severity: {severity}) was triggered")
    if proof_bundle and getattr(proof_bundle, "reproduction_test", None):
        summary_parts.append("a reproduction test was generated to confirm the affected code path")
    summary_parts.append("the Trust Gate evaluated the remediation recommendation")

    summary = (
        "Causal chain: " + " → ".join(summary_parts) + f" (overall confidence: {overall_confidence:.0%})."
        if summary_parts
        else "Insufficient signal to build a full causal chain."
    )

    graph = CausalGraph(
        incident_id=incident_id,
        nodes=nodes,
        edges=edges,
        summary=summary,
        confidence=overall_confidence,
    )
    logger.info(
        "🔗 P6 Causal graph built",
        incident_id=incident_id,
        node_count=len(nodes),
        edge_count=len(edges),
        confidence=overall_confidence,
    )
    return graph
