"""
tests/unit/test_causal_graph.py — P6: Causal Root-Cause Graph
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from responseiq.schemas.causal_graph import CausalGraph, EdgeType, NodeType
from responseiq.services.causal_graph_service import build_causal_graph


# ---------------------------------------------------------------------------
# Helpers / stubs
# ---------------------------------------------------------------------------


@dataclass
class _FakeCorrelation:
    suspect_commit: Optional[str] = "abc1234 fix: cache invalidation"
    suspect_commit_sha: Optional[str] = "abc1234abcdef1234"
    confidence_score: float = 0.85
    suspect_files: List[str] = field(default_factory=lambda: ["src/cache.py"])
    diff_summary: str = "Cache layer missed invalidation on hot path"
    method: str = "heuristic"


@dataclass
class _FakePerfResult:
    regression_detected: bool = True
    passed: bool = False
    delta_pct: float = 22.5
    reason: str = "p95 latency exceeded 15% threshold"


def _fake_proof() -> MagicMock:
    proof = MagicMock()
    proof.reproduction_test.test_path = "tests/repro/test_cache_fix.py"
    proof.reproduction_test.incident_signature = "CacheKeyError"
    proof.reproduction_test.environment_type = "pytest"
    proof.pre_fix_evidence = '{"exit_code": 1}'
    proof.reproduction_confidence = 0.9
    return proof


# ---------------------------------------------------------------------------
# Tests: build_causal_graph
# ---------------------------------------------------------------------------


class TestBuildCausalGraph:
    def test_returns_causal_graph_instance(self):
        g = build_causal_graph(incident_id="INC-001")
        assert isinstance(g, CausalGraph)
        assert g.incident_id == "INC-001"

    def test_empty_signals_has_policy_node_only(self):
        g = build_causal_graph(incident_id="INC-002")
        assert len(g.nodes) == 1
        assert g.nodes[0].type == NodeType.POLICY_DECISION
        assert len(g.edges) == 0

    def test_deploy_event_node_created_from_correlation(self):
        g = build_causal_graph(
            incident_id="INC-003",
            correlation=_FakeCorrelation(),
        )
        node_types = [n.type for n in g.nodes]
        assert NodeType.DEPLOY_EVENT in node_types

    def test_deploy_node_confidence_matches_correlation(self):
        corr = _FakeCorrelation(confidence_score=0.72)
        g = build_causal_graph(incident_id="INC-004", correlation=corr)
        deploy_node = next(n for n in g.nodes if n.type == NodeType.DEPLOY_EVENT)
        assert deploy_node.confidence == 0.72

    def test_latency_spike_node_created_from_perf_result(self):
        g = build_causal_graph(
            incident_id="INC-005",
            correlation=_FakeCorrelation(),
            perf_result=_FakePerfResult(),
        )
        node_types = [n.type for n in g.nodes]
        assert NodeType.LATENCY_SPIKE in node_types

    def test_no_latency_node_when_no_regression(self):
        perf = _FakePerfResult(regression_detected=False)
        g = build_causal_graph(incident_id="INC-006", perf_result=perf)
        node_types = [n.type for n in g.nodes]
        assert NodeType.LATENCY_SPIKE not in node_types

    def test_error_log_node_from_analysis(self):
        g = build_causal_graph(
            incident_id="INC-007",
            analysis_result={"title": "KeyError in payment service", "severity": "high"},
            impact_score=70.0,
        )
        node_types = [n.type for n in g.nodes]
        assert NodeType.ERROR_LOG in node_types

    def test_affected_code_node_from_proof_bundle(self):
        g = build_causal_graph(
            incident_id="INC-008",
            analysis_result={"title": "CacheError", "severity": "high"},
            impact_score=80.0,
            proof_bundle=_fake_proof(),
        )
        node_types = [n.type for n in g.nodes]
        assert NodeType.AFFECTED_CODE in node_types

    def test_full_chain_has_all_node_types(self):
        g = build_causal_graph(
            incident_id="INC-009",
            analysis_result={"title": "DB timeout", "severity": "critical"},
            correlation=_FakeCorrelation(),
            impact_score=90.0,
            perf_result=_FakePerfResult(),
            proof_bundle=_fake_proof(),
        )
        node_types = {n.type for n in g.nodes}
        assert NodeType.DEPLOY_EVENT in node_types
        assert NodeType.LATENCY_SPIKE in node_types
        assert NodeType.ERROR_LOG in node_types
        assert NodeType.AFFECTED_CODE in node_types
        assert NodeType.POLICY_DECISION in node_types

    def test_edges_link_nodes(self):
        g = build_causal_graph(
            incident_id="INC-010",
            analysis_result={"title": "ConnectionError", "severity": "high"},
            correlation=_FakeCorrelation(),
            impact_score=60.0,
        )
        assert len(g.edges) >= 1
        source_ids = {e.source_id for e in g.edges}
        target_ids = {e.target_id for e in g.edges}
        assert "deploy_event" in source_ids
        assert "error_log" in target_ids

    def test_deploy_to_latency_edge_type(self):
        g = build_causal_graph(
            incident_id="INC-011",
            correlation=_FakeCorrelation(),
            perf_result=_FakePerfResult(),
        )
        deploy_to_latency = next(
            (e for e in g.edges if e.source_id == "deploy_event" and e.target_id == "latency_spike"),
            None,
        )
        assert deploy_to_latency is not None
        assert deploy_to_latency.type == EdgeType.CAUSED

    def test_overall_confidence_is_min_of_edges(self):
        g = build_causal_graph(
            incident_id="INC-012",
            analysis_result={"title": "Err", "severity": "low"},
            correlation=_FakeCorrelation(confidence_score=0.6),
            impact_score=40.0,
        )
        edge_confs = [e.confidence for e in g.edges]
        if edge_confs:
            assert g.confidence == pytest.approx(min(edge_confs), abs=0.001)

    def test_summary_non_empty(self):
        g = build_causal_graph(
            incident_id="INC-013",
            analysis_result={"title": "Timeout", "severity": "high"},
            impact_score=55.0,
        )
        assert len(g.summary) > 10

    def test_to_dict_serializable(self):
        g = build_causal_graph(
            incident_id="INC-014",
            analysis_result={"title": "Error", "severity": "medium"},
        )
        d = g.to_dict()
        assert d["incident_id"] == "INC-014"
        assert "nodes" in d
        assert "edges" in d
        assert "summary" in d

    def test_no_correlation_no_deploy_node(self):
        g = build_causal_graph(incident_id="INC-015", correlation=None)
        node_types = [n.type for n in g.nodes]
        assert NodeType.DEPLOY_EVENT not in node_types

    def test_correlation_without_suspect_commit_no_deploy_node(self):
        corr = _FakeCorrelation(suspect_commit=None)
        g = build_causal_graph(incident_id="INC-016", correlation=corr)
        node_types = [n.type for n in g.nodes]
        assert NodeType.DEPLOY_EVENT not in node_types
