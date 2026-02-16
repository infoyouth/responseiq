from responseiq.config import base as config
from responseiq.models.agent_state import AgentState

# Each node function takes AgentState and returns a string outcome


def analyze_node(state: AgentState) -> str:
    # Example: Use context extractor and update state
    # ... (placeholder for actual logic)
    state["investigation_report"] = "Analysis complete."
    return "success"


def synthesize_node(state: AgentState) -> str:
    # Example: Call LLM to generate patch and test
    # ... (placeholder for actual logic)
    state["current_patch"] = "patch_v1"
    return "success"


def verify_node(state: AgentState) -> str:
    # Example: Run test, update state with result
    # ... (placeholder for actual logic)
    result = state.get("last_verification")
    return result if isinstance(result, str) else "fail"


def critique_node(state: AgentState) -> str:
    # Example: Critique last attempt, update attempt_history
    # ... (placeholder for actual logic)
    patch = state.get("current_patch")
    if patch is not None:
        state.setdefault("attempt_history", []).append(patch)
    state["retry_count"] = state.get("retry_count", 0) + 1
    if state["retry_count"] >= config.REMEDIATION_MAX_RETRIES:
        return "max_retries"
    return "retry"
