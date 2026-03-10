# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""DSPy prompt optimisation scaffold.

Uses the ``dspy-ai`` library together with the ResponseIQ fixture set
(``fixtures/fixture_high.json``, ``fixture_medium.json``,
``fixture_none.json``) as training/eval data to compile and optimise
the analysis and remediation prompts automatically.

This module is a **no-op stub** when ``dspy`` is not installed or
``settings.dspy_enabled = False``. The existing ``instructor``-based
prompts remain active and unchanged in that case.

Activation:
    pip install 'responseiq[dspy]'
    RESPONSEIQ_DSPY_ENABLED=true
    responseiq-dspy-optimize   # runs compile + saves optimised prompts

How it works:
    1. Loads fixture JSON as ``dspy.Example`` datasets.
    2. Defines a ``dspy.Signature`` for each prompt (analysis, repro).
    3. Runs ``dspy.BootstrapFewShot`` to select few-shot examples that
       maximise the evaluation metric (severity-match F1).
    4. Saves the compiled program to ``~/.responseiq/dspy_compiled.json``.
    5. On startup, ``llm_service.py`` loads the compiled program when
       ``RESPONSEIQ_DSPY_ENABLED=true`` and injects the optimised prompts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from responseiq.utils.logger import logger

# ---------------------------------------------------------------------------
# DSPy Signatures (defined unconditionally — they're plain Python classes)
# ---------------------------------------------------------------------------

_COMPILED_PROGRAM_PATH = Path.home() / ".responseiq" / "dspy_compiled.json"


def _load_fixtures() -> list[dict[str, Any]]:
    """Load all fixture files as a flat list of examples."""
    root = Path(__file__).parent.parent.parent.parent  # repo root
    examples = []
    for fname in ("fixture_high.json", "fixture_medium.json", "fixture_none.json"):
        path = root / "fixtures" / fname
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        if isinstance(data, list):
            examples.extend(data)
        elif isinstance(data, dict):
            examples.append(data)
    return examples


def is_available() -> bool:
    """Return True when dspy-ai is installed and RESPONSEIQ_DSPY_ENABLED=true."""
    try:
        from responseiq.config.settings import settings

        if not getattr(settings, "dspy_enabled", False):
            return False
        import dspy  # type: ignore[import-untyped]  # noqa: F401

        return True
    except ImportError:
        return False


def compile_prompts(max_bootstrapped_demos: int = 3) -> Optional[Path]:
    """
    Run DSPy BootstrapFewShot optimisation and save the compiled program.

    Returns the path to the saved program file, or ``None`` on failure.
    This may take several minutes on first run — it performs live LLM calls.
    """
    if not is_available():
        logger.warning(
            "DSPy optimisation skipped — install 'responseiq[dspy]' and set RESPONSEIQ_DSPY_ENABLED=true to enable."
        )
        return None

    import dspy  # type: ignore[import-untyped]

    from responseiq.config.settings import settings

    # Configure DSPy LM backend from existing settings
    if settings.openai_api_key:
        api_key = settings.openai_api_key.get_secret_value()
        lm = dspy.LM(model="openai/gpt-4o-mini", api_key=api_key)
    elif settings.llm_base_url:
        lm = dspy.LM(model="openai/local", base_url=str(settings.llm_base_url), api_key="ollama")
    else:
        logger.error("DSPy compile requires an LLM — configure RESPONSEIQ_OPENAI_API_KEY.")
        return None

    dspy.configure(lm=lm)

    # ── Signature ────────────────────────────────────────────────────────
    class IncidentAnalysisSignature(dspy.Signature):  # type: ignore[misc]
        """Analyse a log entry and return severity, title, and remediation."""

        log_text: str = dspy.InputField(desc="Raw log text or stack trace")
        severity: str = dspy.OutputField(desc="One of: critical, high, medium, low")
        title: str = dspy.OutputField(desc="One-line incident title")
        remediation: str = dspy.OutputField(desc="Concrete remediation steps")

    # ── Training examples from fixtures ──────────────────────────────────
    raw_examples = _load_fixtures()
    if not raw_examples:
        logger.error("No fixture data found — cannot compile DSPy program.")
        return None

    train_set = []
    for ex in raw_examples:
        log = ex.get("message") or ex.get("log") or ex.get("text") or ""
        if not log:
            continue
        train_set.append(
            dspy.Example(
                log_text=log,
                severity=ex.get("expected_severity", "medium"),
                title=ex.get("expected_title", ""),
                remediation=ex.get("expected_remediation", ""),
            ).with_inputs("log_text")
        )

    if len(train_set) < 2:
        logger.warning("Too few training examples — need at least 2. Add more fixture data.")
        return None

    # ── Evaluation metric: severity-match accuracy ────────────────────────
    def _severity_match(example: dspy.Example, prediction: Any, trace: Any = None) -> bool:
        return str(example.severity).lower() == str(prediction.severity).lower()

    # ── Compile ───────────────────────────────────────────────────────────
    logger.info(f"DSPy: compiling with {len(train_set)} examples, max_demos={max_bootstrapped_demos}")
    teleprompter = dspy.BootstrapFewShot(
        metric=_severity_match,
        max_bootstrapped_demos=max_bootstrapped_demos,
    )
    program = dspy.Predict(IncidentAnalysisSignature)
    compiled = teleprompter.compile(program, trainset=train_set)

    # ── Save ──────────────────────────────────────────────────────────────
    _COMPILED_PROGRAM_PATH.parent.mkdir(parents=True, exist_ok=True)
    compiled.save(str(_COMPILED_PROGRAM_PATH))
    logger.info(f"DSPy compiled program saved → {_COMPILED_PROGRAM_PATH}")
    return _COMPILED_PROGRAM_PATH


def load_compiled_program() -> Optional[Any]:
    """
    Load a previously compiled DSPy program from disk.

    Returns the program object (callable as ``program(log_text=...)``),
    or ``None`` if no compiled program exists or DSPy is not available.
    """
    if not is_available():
        return None
    if not _COMPILED_PROGRAM_PATH.exists():
        return None

    import dspy  # type: ignore[import-untyped]

    class IncidentAnalysisSignature(dspy.Signature):  # type: ignore[misc]
        """Analyse a log entry and return severity, title, and remediation."""

        log_text: str = dspy.InputField(desc="Raw log text or stack trace")
        severity: str = dspy.OutputField(desc="One of: critical, high, medium, low")
        title: str = dspy.OutputField(desc="One-line incident title")
        remediation: str = dspy.OutputField(desc="Concrete remediation steps")

    program = dspy.Predict(IncidentAnalysisSignature)
    program.load(str(_COMPILED_PROGRAM_PATH))
    logger.info("DSPy compiled program loaded")
    return program
