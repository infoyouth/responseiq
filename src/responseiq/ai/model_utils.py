# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Cost-efficient multi-LLM model routing.

``LLMRouter`` dispatches each task (detect, analyze, generate_patch) to
the right model tier — cheap fast models for classification, stronger
models for patch synthesis. The routing table rebuilds from settings on
each instantiation, so environment overrides are always respected.

Example:
    ```python
    from responseiq.ai.model_utils import router as _router

    model = _router.model_for("analyze")  # "gpt-4o" by default
    model = _router.model_for("detect")   # "gpt-4o-mini" by default
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from responseiq.config.settings import settings

# ── task → category mapping ──────────────────────────────────────────────────

#: Cheap, fast tasks — detection and classification only.
FAST_TASKS: frozenset[str] = frozenset({"detect", "classify_severity", "classify"})

#: Expensive tasks — patch synthesis and deep incident analysis.
PATCH_TASKS: frozenset[str] = frozenset({"generate_patch", "analyze", "analyze_incident"})

#: Code-generation tasks — reproduction test synthesis.
REPRO_TASKS: frozenset[str] = frozenset({"generate_repro", "generate_repro_test"})


# ── router ───────────────────────────────────────────────────────────────────


@dataclass
class LLMRouter:
    """Maps task names to the correct model, respecting live settings values.

    A module-level singleton ``router`` is exported for convenience.  Tests
    that need strict isolation can build their own ``LLMRouter()`` instance or
    call ``override()`` on the singleton and restore afterwards.
    """

    _routing_table: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # _routing_table holds ONLY explicit overrides (set via override()).
        # Standard category-based routing reads live from settings in model_for().
        pass

    def _rebuild(self) -> None:
        """Clear any cached overrides and rebuild from settings (call after settings change)."""
        self._routing_table.clear()

    def model_for(self, task: str) -> str:
        """Return the model name for *task*.

        Reads *live* settings values on every call so that runtime overrides
        (env vars, test patches of ``responseiq.ai.model_utils.settings``) are
        always respected.

        ``_routing_table`` overrides (set via ``override()``) take precedence
        over live settings — this lets tests pin individual tasks without
        touching global settings.

        Falls back to ``settings.llm_analysis_model`` for unknown tasks.

        Args:
            task: One of the known task keys or any string for fallback.

        Returns:
            Model name string (e.g. ``"gpt-4o-mini"`` or ``"gpt-4o"``).
        """
        # Explicit per-task override (set via override()) wins first
        if task in self._routing_table:
            return self._routing_table[task]
        # Live settings fallback by category
        if task in FAST_TASKS:
            return settings.llm_fast_model
        if task in REPRO_TASKS:
            return settings.llm_repro_model
        return settings.llm_analysis_model

    def override(self, task: str, model: str) -> None:
        """Override a single task mapping.

        Useful in tests and local experimentation without touching settings.

        Args:
            task:  Task key to override.
            model: Model name to use for this task.
        """
        self._routing_table[task] = model

    def table(self) -> Dict[str, str]:
        """Return a full snapshot of the current routing (live settings + explicit overrides).

        Useful for audit-trail logging. Explicit ``override()`` entries win.
        The result is a plain ``dict[str, str]`` safe to log or serialise.
        """
        live: Dict[str, str] = {
            **{task: settings.llm_fast_model for task in FAST_TASKS},
            **{task: settings.llm_analysis_model for task in PATCH_TASKS},
            **{task: settings.llm_repro_model for task in REPRO_TASKS},
        }
        live.update(self._routing_table)  # explicit overrides win
        return live


# ── module-level singleton  ────────────────────────────────────────────────
router = LLMRouter()
