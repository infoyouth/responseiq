from abc import ABC, abstractmethod


class BasePlugin(ABC):
    @abstractmethod
    def run(self, agent_state: dict) -> dict:
        """Run the plugin with the provided AgentState. Returns updated state (delta pattern)."""
        pass
