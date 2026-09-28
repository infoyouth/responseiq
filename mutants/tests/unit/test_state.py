"""
Unit tests for AgentState TypedDict.
"""

from responseiq.models.agent_state import AgentState


def test_agentstate_fields():
    state: AgentState = {
        "attempt_history": ["patch1"],
        "retry_count": 1,
        "incident_id": "INC123",
        "investigation_report": "done",
        "current_patch": "patch1",
        "last_verification": "pass",
        "status": "complete",
    }
    assert state["incident_id"] == "INC123"
    assert state["status"] == "complete"
    assert state["last_verification"] == "pass"
    assert isinstance(state["attempt_history"], list)
    assert state["retry_count"] == 1
