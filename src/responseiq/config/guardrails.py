"""
guardrails.py — P4: Sovereign Architectural Guardrails

Checks proposed code changes against a project-level rule set defined in
`.responseiq/rules.yaml` before the Trust Gate allows any execution.

State-machine position:
    Detect → Context → Reason → **Policy (P4 Guardrails here)** → Execute → Learn

Integration point: `TrustGateValidator._validate_guardrails()`.

Actions
-------
block               → TrustGate denies the remediation (DenyReason.GUARDRAIL_VIOLATION).
downgrade_to_pr_only→ Execution mode silently forced to PR_ONLY.
warn                → Logged in audit trail; does not block or downgrade.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from responseiq.utils.logger import logger

# ---------------------------------------------------------------------------
# Rule schema
# ---------------------------------------------------------------------------


@dataclass
class GuardrailRule:
    """A single architectural rule from .responseiq/rules.yaml."""

    id: str
    description: str
    action: str  # "block" | "downgrade_to_pr_only" | "warn"
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        valid_actions = {"block", "downgrade_to_pr_only", "warn"}
        if self.action not in valid_actions:
            raise ValueError(
                f"GuardrailRule '{self.id}': invalid action '{self.action}'. Must be one of {valid_actions}"
            )


@dataclass
class GuardrailsConfig:
    """Complete set of guardrail rules loaded from a YAML file."""

    rules: List[GuardrailRule] = field(default_factory=list)
    version: str = "1"

    @classmethod
    def load(cls, path: Path) -> "GuardrailsConfig":
        """Load rules from a YAML file.  Requires PyYAML (already in deps via pre-commit)."""
        try:
            import yaml  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "PyYAML is required for GuardrailsConfig.load(). Install with: pip install pyyaml"
            ) from exc

        with open(path) as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise ValueError(f"Invalid guardrails config at {path}: expected a YAML mapping")

        version = str(raw.get("version", "1"))
        rules: List[GuardrailRule] = []
        for rule_dict in raw.get("rules", []):
            rules.append(
                GuardrailRule(
                    id=rule_dict["id"],
                    description=rule_dict["description"],
                    action=rule_dict["action"],
                    enabled=rule_dict.get("enabled", True),
                    config=rule_dict.get("config") or {},
                )
            )

        logger.info(f"GuardrailsConfig loaded {len(rules)} rules from {path}")
        return cls(rules=rules, version=version)

    @classmethod
    def default(cls) -> "GuardrailsConfig":
        """Return a sensible baseline config (used when no YAML file is present)."""
        return cls(
            rules=[
                GuardrailRule(
                    id="no_bare_except", description="No bare except: clauses", action="downgrade_to_pr_only"
                ),
                GuardrailRule(
                    id="no_hardcoded_secrets", description="No hardcoded secrets or API keys", action="block"
                ),
                GuardrailRule(id="no_print_statements", description="Use logger instead of print()", action="warn"),
            ]
        )

    def enabled_rules(self) -> List[GuardrailRule]:
        return [r for r in self.rules if r.enabled]


# ---------------------------------------------------------------------------
# Violation schema
# ---------------------------------------------------------------------------


@dataclass
class GuardrailViolation:
    """A single rule violation found in proposed code changes."""

    rule_id: str
    description: str
    action: str
    evidence: str  # The offending snippet (truncated to 200 chars)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "description": self.description,
            "action": self.action,
            "evidence": self.evidence,
        }


@dataclass
class GuardrailsResult:
    """Aggregate result of running all enabled guardrail rules."""

    violations: List[GuardrailViolation] = field(default_factory=list)  # action=block
    downgrades: List[GuardrailViolation] = field(default_factory=list)  # action=downgrade_to_pr_only
    warnings: List[GuardrailViolation] = field(default_factory=list)  # action=warn
    checked_rules: List[str] = field(default_factory=list)

    @property
    def has_blocking_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def has_downgrades(self) -> bool:
        return len(self.downgrades) > 0

    @property
    def all_violations(self) -> List[GuardrailViolation]:
        return self.violations + self.downgrades + self.warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checked_rules": self.checked_rules,
            "blocking_violations": [v.to_dict() for v in self.violations],
            "downgrades": [d.to_dict() for d in self.downgrades],
            "warnings": [w.to_dict() for w in self.warnings],
        }


# ---------------------------------------------------------------------------
# Regex patterns used by individual rule checkers
# ---------------------------------------------------------------------------

_RE_BARE_EXCEPT = re.compile(r"except\s*:")
_RE_FUNC_DEF = re.compile(r"def\s+\w+\s*\([^)]*\)(?!\s*->)")  # def foo(...) without ->
_RE_HARDCODED_SECRET = re.compile(
    r"(?i)(?:"
    r'api[_-]?key\s*=\s*["\'][^"\']{8,}'
    r'|password\s*=\s*["\'][^"\']{4,}'
    r'|secret\s*=\s*["\'][^"\']{6,}'
    r'|token\s*=\s*["\'][^"\']{8,}'
    r"|sk-[A-Za-z0-9]{20,}"  # OpenAI key
    r"|Bearer\s+[A-Za-z0-9\-_]{20,}"  # Bearer token
    r"|AKIA[0-9A-Z]{16}"  # AWS access key
    r")"
)
_RE_PRINT = re.compile(r"\bprint\s*\(")
_RE_OS_SYSTEM = re.compile(r"\bos\.system\s*\(")
_RE_SUBPROCESS_SHELL = re.compile(r"\bsubprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True")
_RE_MUTABLE_DEFAULT = re.compile(r"def\s+\w+\s*\([^)]*=\s*(?:\[\s*\]|\{\s*\}|set\s*\(\s*\))")


# ---------------------------------------------------------------------------
# Core checker
# ---------------------------------------------------------------------------


class GuardrailChecker:
    """
    Runs all enabled guardrail rules against the text content of proposed changes.
    """

    def __init__(self, config: GuardrailsConfig):
        self.config = config
        self._rule_checkers: Dict[str, Callable[[GuardrailRule, str], Optional[str]]] = {
            "no_bare_except": self._check_no_bare_except,
            "require_type_annotations": self._check_require_type_annotations,
            "no_hardcoded_secrets": self._check_no_hardcoded_secrets,
            "no_print_statements": self._check_no_print_statements,
            "no_new_heavy_dependencies": self._check_no_new_heavy_dependencies,
            "no_direct_os_system": self._check_no_direct_os_system,
            "no_mutable_default_args": self._check_no_mutable_default_args,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(
        self,
        proposed_changes: List[Dict[str, Any]],
        affected_files: Optional[List[str]] = None,
    ) -> GuardrailsResult:
        """
        Run all enabled rules against the text content extracted from proposed_changes.

        Parameters
        ----------
        proposed_changes : list of dicts, each may have any string-valued fields
                           (description, code, patch, diff, command, etc.)
        affected_files   : list of file paths (used for file-level rules)
        """
        content = self._extract_content(proposed_changes, affected_files or [])
        result = GuardrailsResult()

        for rule in self.config.enabled_rules():
            result.checked_rules.append(rule.id)
            checker = self._rule_checkers.get(rule.id)
            if checker is None:
                logger.debug(f"GuardrailChecker: no checker registered for rule '{rule.id}' — skipping")
                continue

            evidence = checker(rule, content)
            if evidence is not None:
                violation = GuardrailViolation(
                    rule_id=rule.id,
                    description=rule.description,
                    action=rule.action,
                    evidence=evidence[:200],
                )
                if rule.action == "block":
                    result.violations.append(violation)
                    logger.warning(f"Guardrail BLOCK [{rule.id}]: {evidence[:80]!r}")
                elif rule.action == "downgrade_to_pr_only":
                    result.downgrades.append(violation)
                    logger.warning(f"Guardrail DOWNGRADE [{rule.id}]: {evidence[:80]!r}")
                else:  # warn
                    result.warnings.append(violation)
                    logger.info(f"Guardrail WARN [{rule.id}]: {evidence[:80]!r}")
            else:
                logger.debug(f"Guardrail PASS [{rule.id}]")

        return result

    # ------------------------------------------------------------------
    # Content extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_content(
        proposed_changes: List[Dict[str, Any]],
        affected_files: List[str],
    ) -> str:
        """
        Flatten all string values from proposed_changes dicts into a single
        text blob for pattern matching.  Joins affected_files on separate lines
        so file-path rules can match.
        """
        parts: List[str] = []

        for change in proposed_changes:
            if not isinstance(change, dict):
                continue
            for val in change.values():
                if isinstance(val, str):
                    parts.append(val)
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, str):
                            parts.append(item)

        # Include affected file paths so file-extension rules can fire
        parts.extend(affected_files)

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Individual rule checkers — return evidence string or None (pass)
    # ------------------------------------------------------------------

    @staticmethod
    def _check_no_bare_except(_rule: GuardrailRule, content: str) -> Optional[str]:
        m = _RE_BARE_EXCEPT.search(content)
        return m.group(0) if m else None

    @staticmethod
    def _check_require_type_annotations(_rule: GuardrailRule, content: str) -> Optional[str]:
        # Only flag if there IS a function def AND it lacks a return annotation
        m = _RE_FUNC_DEF.search(content)
        if m:
            # Make sure it's not a class __init__ (no return annotation expected)
            snippet = m.group(0)
            if "__init__" not in snippet and "__new__" not in snippet:
                return snippet
        return None

    @staticmethod
    def _check_no_hardcoded_secrets(_rule: GuardrailRule, content: str) -> Optional[str]:
        m = _RE_HARDCODED_SECRET.search(content)
        return m.group(0) if m else None

    @staticmethod
    def _check_no_print_statements(_rule: GuardrailRule, content: str) -> Optional[str]:
        m = _RE_PRINT.search(content)
        return m.group(0) if m else None

    @staticmethod
    def _check_no_new_heavy_dependencies(rule: GuardrailRule, content: str) -> Optional[str]:
        blocked: List[str] = rule.config.get("blocked_imports", [])
        for pkg in blocked:
            pattern = re.compile(rf"\b(?:import|from)\s+{re.escape(pkg)}\b")
            m = pattern.search(content)
            if m:
                return m.group(0)
        return None

    @staticmethod
    def _check_no_direct_os_system(_rule: GuardrailRule, content: str) -> Optional[str]:
        m = _RE_OS_SYSTEM.search(content) or _RE_SUBPROCESS_SHELL.search(content)
        return m.group(0) if m else None

    @staticmethod
    def _check_no_mutable_default_args(_rule: GuardrailRule, content: str) -> Optional[str]:
        m = _RE_MUTABLE_DEFAULT.search(content)
        return m.group(0) if m else None
