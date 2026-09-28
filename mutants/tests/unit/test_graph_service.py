"""
Unit tests for StateGraph (LangGraph-inspired cyclic agent).
"""

from responseiq.models.agent_state import AgentState
from responseiq.services.graph_service import StateGraph


def test_stategraph_simple_cycle():
    state: AgentState = {"retry_count": 0, "attempt_history": []}
    graph = StateGraph(state)

    def node_a(s):
        s["attempt_history"].append("A")
        return "to_b"

    def node_b(s):
        s["attempt_history"].append("B")
        return "to_a" if s["retry_count"] < 2 else "done"

    graph.add_node("A", node_a)
    graph.add_node("B", node_b)
    graph.add_edge("A", "B", "to_b")
    graph.add_edge("B", "A", "to_a")
    graph.add_edge("B", None, "done")
    graph.set_start("A")
    state["retry_count"] = 0

    # Simulate increment in node_b
    def node_b_with_retry(s):
        s["attempt_history"].append("B")
        s["retry_count"] += 1
        return "to_a" if s["retry_count"] < 2 else "done"

    graph.nodes["B"] = node_b_with_retry
    graph.run()
    assert state["retry_count"] == 2
    assert state["attempt_history"] == ["A", "B", "A", "B"]
