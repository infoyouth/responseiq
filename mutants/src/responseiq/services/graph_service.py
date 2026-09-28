# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Lightweight state-machine graph for the remediation pipeline.

Builds a directed node graph where each node is a callable that
receives the current ``AgentState`` and returns a transition string.
Edges map transition strings to the next node name.
"""

from typing import Callable, Dict, Optional

from responseiq.models.agent_state import AgentState


class StateGraph:
    def __init__(self, initial_state: AgentState):
        self.state = initial_state
        self.nodes: Dict[str, Callable[[AgentState], str]] = {}
        self.node_models: Dict[str, str] = {}  # node_name -> model_id
        self.edges: Dict[str, Dict[str, str]] = {}
        self.current_node: Optional[str] = None

    def add_node(self, name: str, func: Callable[[AgentState], str], model: Optional[str] = None):
        self.nodes[name] = func
        if model:
            self.node_models[name] = model

    def add_edge(self, from_node: str, to_node: str, condition: str):
        if from_node not in self.edges:
            self.edges[from_node] = {}
        self.edges[from_node][condition] = to_node

    def set_start(self, node: str):
        self.current_node = node

    def run(self):
        while self.current_node:
            node_func = self.nodes[self.current_node]
            # model = self.node_models.get(self.current_node)  # For future extension
            # outcome = node_func(self.state, model=model)  # For future extension
            outcome = node_func(self.state)
            next_node = self.edges.get(self.current_node, {}).get(outcome)
            if next_node:
                self.current_node = next_node
            else:
                break


# Example model map for hybrid tiering:
# MODEL_MAP = {
#     "analyze_node": "gemini-1.5-pro",
#     "synthesize_node": "gemini-1.5-pro",
#     "verify_node": "gemini-1.5-flash",
#     "critique_node": "gemini-1.5-flash",
# }
# graph.add_node("analyze_node", analyze_node, model=MODEL_MAP["analyze_node"])
