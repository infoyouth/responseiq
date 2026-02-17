from .base import BasePlugin


class ScanPlugin(BasePlugin):
    def run(self, agent_state: dict) -> dict:
        # Example: scan logic here, update agent_state as needed
        agent_state = agent_state.copy()
        agent_state["scan_result"] = "success"  # Placeholder
        return agent_state
