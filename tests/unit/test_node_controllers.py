"""
Unit tests for node_controllers (LangGraph node logic).
"""

from responseiq.models.agent_state import AgentState
from responseiq.services.node_controllers import (
    analyze_node,
    critique_node,
    synthesize_node,
    verify_node,
)


def test_analyze_node_sets_report():
    state: AgentState = {}
    result = analyze_node(state)
    assert result == "success"
    assert state["investigation_report"] == "Analysis complete."


def test_synthesize_node_sets_patch():
    state: AgentState = {}
    result = synthesize_node(state)
    assert result == "success"
    assert state["current_patch"] == "patch_v1"


def test_verify_node_returns_fail():
    state: AgentState = {"last_verification": "fail"}
    result = verify_node(state)
    assert result == "fail"


def test_verify_node_returns_pass():
    state: AgentState = {"last_verification": "pass"}
    result = verify_node(state)
    assert result == "pass"


def test_critique_node_retry_and_max():
    state: AgentState = {"current_patch": "patch_v1", "retry_count": 2}
    result = critique_node(state)
    assert result == "max_retries"
    assert state["retry_count"] == 3
    assert state["attempt_history"] == ["patch_v1"]
    # Test retry path
    state = {"current_patch": "patch_v2", "retry_count": 0}
    result = critique_node(state)
    assert result == "retry"
    assert state["retry_count"] == 1
    assert state["attempt_history"] == ["patch_v2"]
