from responseiq.config import base as config
from responseiq.models.agent_state import AgentState
from responseiq.services.prompt_loader import load_prompts

NODE_PROMPTS = load_prompts()

# Each node function takes AgentState and returns a string outcome


def analyze_node(state: AgentState) -> str:
    # ... LLM call would use prompt here ...
    # Example: state["investigation_report"] = llm_response_json
    state["investigation_report"] = "Analysis complete."
    return "success"


def synthesize_node(state: AgentState) -> str:
    # ... LLM call would use prompt here ...
    # Example: llm_output = call_llm(prompt)
    # patch = extract_tag_block(llm_output, "PATCH")
    # test = extract_tag_block(llm_output, "REPRO_TEST")
    state["current_patch"] = "patch_v1"
    return "success"


def verify_node(state: AgentState) -> str:
    # ... LLM call would use prompt here ...
    result = state.get("last_verification")
    return result if isinstance(result, str) else "fail"


def critique_node(state: AgentState) -> str:
    # ... LLM call would use prompt here ...
    patch = state.get("current_patch")
    if patch is not None:
        state.setdefault("attempt_history", []).append(patch)
    state["retry_count"] = state.get("retry_count", 0) + 1
    if state["retry_count"] >= config.REMEDIATION_MAX_RETRIES:
        return "max_retries"
    return "retry"
