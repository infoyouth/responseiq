from typing import Callable, Dict, Optional

from responseiq.models.agent_state import AgentState


class StateGraph:
    def __init__(self, initial_state: AgentState):
        self.state = initial_state
        self.nodes: Dict[str, Callable[[AgentState], str]] = {}
        self.edges: Dict[str, Dict[str, str]] = {}
        self.current_node: Optional[str] = None

    def add_node(self, name: str, func: Callable[[AgentState], str]):
        self.nodes[name] = func

    def add_edge(self, from_node: str, to_node: str, condition: str):
        if from_node not in self.edges:
            self.edges[from_node] = {}
        self.edges[from_node][condition] = to_node

    def set_start(self, node: str):
        self.current_node = node

    def run(self):
        while self.current_node:
            node_func = self.nodes[self.current_node]
            outcome = node_func(self.state)
            next_node = self.edges.get(self.current_node, {}).get(outcome)
            if next_node:
                self.current_node = next_node
            else:
                break
