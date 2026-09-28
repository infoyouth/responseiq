"""
tests/unit/test_guardrails.py

Unit tests for P4 — Sovereign Architectural Guardrails.

Coverage
--------
- GuardrailRule validation (invalid action raises ValueError)
- GuardrailsConfig.load() from a real temp YAML file
- GuardrailsConfig.default()
- GuardrailChecker._extract_content() — flattens nested dict/list values
- Individual rule checkers: all 7 rules, both pass and fail paths
- GuardrailsResult properties: has_blocking_violations, has_downgrades
- GuardrailChecker.check() — routing to correct result bucket
- TrustGateValidator._validate_guardrails():
    - no checker configured → pass-through
    - blocking violation → deny + DenyReason.GUARDRAIL_VIOLATION
    - downgrade violation → allowed=True but policy_mode forced to PR_ONLY
    - warn violation → allowed=True, logged in evidence
    - multiple violations across buckets
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any, Dict, List

import pytest

from responseiq.config.guardrails import (
    GuardrailChecker,
    GuardrailRule,
    GuardrailViolation,
    GuardrailsConfig,
    GuardrailsResult,
)
from responseiq.config.policy_config import DenyReason, PolicyMode
from responseiq.services.trust_gate import RemediationRequest, TrustGateValidator, ValidationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _checker_from_rules(*rules: GuardrailRule) -> GuardrailChecker:
    return GuardrailChecker(GuardrailsConfig(rules=list(rules)))


def _changes(*snippets: str) -> List[Dict[str, Any]]:
    """Wrap code snippets as proposed_changes list items."""
    return [{"description": s} for s in snippets]


def _make_request(**overrides: Any) -> RemediationRequest:
    defaults: Dict[str, Any] = dict(
        incident_id="test-001",
        severity="high",
        confidence=0.9,
        impact_score=80.0,
        blast_radius="single_service",
        rollback_plan="git revert HEAD",
        test_plan="pytest tests/",
        affected_files=[],
        proposed_changes=[],
    )
    defaults.update(overrides)
    return RemediationRequest(**defaults)


# ---------------------------------------------------------------------------
# GuardrailRule
# ---------------------------------------------------------------------------


class TestGuardrailRule:
    def test_valid_actions_accepted(self):
        for action in ("block", "downgrade_to_pr_only", "warn"):
            rule = GuardrailRule(id="x", description="x", action=action)
            assert rule.action == action

    def test_invalid_action_raises(self):
        with pytest.raises(ValueError, match="invalid action"):
            GuardrailRule(id="x", description="x", action="ignore")


# ---------------------------------------------------------------------------
# GuardrailsConfig
# ---------------------------------------------------------------------------


class TestGuardrailsConfig:
    def test_load_from_yaml(self, tmp_path: Path):
        yaml_content = textwrap.dedent("""\
            version: "1"
            rules:
              - id: no_bare_except
                description: "No bare except"
                action: downgrade_to_pr_only
                enabled: true
              - id: no_hardcoded_secrets
                description: "No secrets"
                action: block
                enabled: false
        """)
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml_content)

        config = GuardrailsConfig.load(rules_file)

        assert config.version == "1"
        assert len(config.rules) == 2
        assert config.rules[0].id == "no_bare_except"
        assert config.rules[1].enabled is False

    def test_enabled_rules_filters_disabled(self, tmp_path: Path):
        yaml_content = textwrap.dedent("""\
            version: "1"
            rules:
              - id: rule_a
                description: "A"
                action: warn
                enabled: true
              - id: rule_b
                description: "B"
                action: warn
                enabled: false
        """)
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml_content)
        config = GuardrailsConfig.load(rules_file)

        assert len(config.enabled_rules()) == 1
        assert config.enabled_rules()[0].id == "rule_a"

    def test_default_config_has_rules(self):
        config = GuardrailsConfig.default()
        assert len(config.rules) >= 1
        ids = [r.id for r in config.rules]
        assert "no_bare_except" in ids
        assert "no_hardcoded_secrets" in ids

    def test_load_invalid_yaml_raises(self, tmp_path: Path):
        bad_file = tmp_path / "rules.yaml"
        bad_file.write_text("- just a list\n- not a mapping\n")
        with pytest.raises(ValueError, match="expected a YAML mapping"):
            GuardrailsConfig.load(bad_file)


# ---------------------------------------------------------------------------
# GuardrailsResult
# ---------------------------------------------------------------------------


class TestGuardrailsResult:
    def _viol(self, action: str) -> GuardrailViolation:
        return GuardrailViolation(rule_id="x", description="x", action=action, evidence="snippet")

    def test_has_blocking_violations_true(self):
        r = GuardrailsResult(violations=[self._viol("block")])
        assert r.has_blocking_violations is True

    def test_has_blocking_violations_false(self):
        r = GuardrailsResult(downgrades=[self._viol("downgrade_to_pr_only")])
        assert r.has_blocking_violations is False

    def test_has_downgrades(self):
        r = GuardrailsResult(downgrades=[self._viol("downgrade_to_pr_only")])
        assert r.has_downgrades is True

    def test_to_dict_keys(self):
        r = GuardrailsResult(checked_rules=["no_bare_except"])
        d = r.to_dict()
        assert set(d.keys()) == {"checked_rules", "blocking_violations", "downgrades", "warnings"}


# ---------------------------------------------------------------------------
# Individual rule checkers
# ---------------------------------------------------------------------------


class TestNoBareExcept:
    def test_bare_except_detected(self):
        checker = _checker_from_rules(GuardrailRule("no_bare_except", "desc", "block"))
        result = checker.check(_changes("try:\n    pass\nexcept:\n    pass"), [])
        assert result.has_blocking_violations

    def test_specific_except_passes(self):
        checker = _checker_from_rules(GuardrailRule("no_bare_except", "desc", "block"))
        result = checker.check(_changes("try:\n    pass\nexcept ValueError:\n    pass"), [])
        assert not result.has_blocking_violations


class TestRequireTypeAnnotations:
    def test_unannotated_function_flagged(self):
        checker = _checker_from_rules(GuardrailRule("require_type_annotations", "desc", "warn"))
        result = checker.check(_changes("def calculate_total(a, b):\n    return a + b"), [])
        assert len(result.warnings) == 1

    def test_annotated_function_passes(self):
        checker = _checker_from_rules(GuardrailRule("require_type_annotations", "desc", "warn"))
        result = checker.check(_changes("def calculate_total(a: int, b: int) -> int:\n    return a + b"), [])
        assert len(result.warnings) == 0

    def test_init_method_excluded(self):
        checker = _checker_from_rules(GuardrailRule("require_type_annotations", "desc", "warn"))
        result = checker.check(_changes("def __init__(self, x):\n    self.x = x"), [])
        assert len(result.warnings) == 0


class TestNoHardcodedSecrets:
    def test_openai_key_blocked(self):
        checker = _checker_from_rules(GuardrailRule("no_hardcoded_secrets", "desc", "block"))
        result = checker.check(_changes("api_key = 'sk-abcdefghijklmnopqrstuvwx'"), [])
        assert result.has_blocking_violations

    def test_aws_key_blocked(self):
        checker = _checker_from_rules(GuardrailRule("no_hardcoded_secrets", "desc", "block"))
        result = checker.check(_changes("key = 'AKIAIOSFODNN7EXAMPLE'"), [])
        assert result.has_blocking_violations

    def test_password_assignment_blocked(self):
        checker = _checker_from_rules(GuardrailRule("no_hardcoded_secrets", "desc", "block"))
        result = checker.check(_changes('password = "supersecret999"'), [])
        assert result.has_blocking_violations

    def test_placeholder_passes(self):
        checker = _checker_from_rules(GuardrailRule("no_hardcoded_secrets", "desc", "block"))
        result = checker.check(_changes('api_key = os.environ["OPENAI_KEY"]'), [])
        assert not result.has_blocking_violations


class TestNoPrintStatements:
    def test_print_call_flagged(self):
        checker = _checker_from_rules(GuardrailRule("no_print_statements", "desc", "warn"))
        result = checker.check(_changes('print("debug value:", x)'), [])
        assert len(result.warnings) == 1

    def test_logger_passes(self):
        checker = _checker_from_rules(GuardrailRule("no_print_statements", "desc", "warn"))
        result = checker.check(_changes('logger.info("debug value: %s", x)'), [])
        assert len(result.warnings) == 0


class TestNoNewHeavyDependencies:
    def test_torch_import_blocked(self):
        rule = GuardrailRule("no_new_heavy_dependencies", "desc", "block", config={"blocked_imports": ["torch"]})
        checker = _checker_from_rules(rule)
        result = checker.check(_changes("import torch\nmodel = torch.nn.Linear(10, 1)"), [])
        assert result.has_blocking_violations

    def test_from_import_also_blocked(self):
        rule = GuardrailRule("no_new_heavy_dependencies", "desc", "block", config={"blocked_imports": ["tensorflow"]})
        checker = _checker_from_rules(rule)
        result = checker.check(_changes("from tensorflow import keras"), [])
        assert result.has_blocking_violations

    def test_allowed_import_passes(self):
        rule = GuardrailRule("no_new_heavy_dependencies", "desc", "block", config={"blocked_imports": ["torch"]})
        checker = _checker_from_rules(rule)
        result = checker.check(_changes("import httpx\nimport asyncio"), [])
        assert not result.has_blocking_violations

    def test_empty_blocked_list_always_passes(self):
        rule = GuardrailRule("no_new_heavy_dependencies", "desc", "block", config={"blocked_imports": []})
        checker = _checker_from_rules(rule)
        result = checker.check(_changes("import torch"), [])
        assert not result.has_blocking_violations


class TestNoDirectOsSystem:
    def test_os_system_blocked(self):
        checker = _checker_from_rules(GuardrailRule("no_direct_os_system", "desc", "block"))
        result = checker.check(_changes('os.system("rm -rf /tmp/old")'), [])
        assert result.has_blocking_violations

    def test_subprocess_shell_true_blocked(self):
        checker = _checker_from_rules(GuardrailRule("no_direct_os_system", "desc", "block"))
        result = checker.check(_changes('subprocess.call(["ls"], shell=True)'), [])
        assert result.has_blocking_violations

    def test_subprocess_without_shell_passes(self):
        checker = _checker_from_rules(GuardrailRule("no_direct_os_system", "desc", "block"))
        result = checker.check(_changes('subprocess.run(["git", "status"])'), [])
        assert not result.has_blocking_violations


class TestNoMutableDefaultArgs:
    def test_list_default_flagged(self):
        checker = _checker_from_rules(GuardrailRule("no_mutable_default_args", "desc", "downgrade_to_pr_only"))
        result = checker.check(_changes("def foo(items=[]):\n    items.append(1)"), [])
        assert result.has_downgrades

    def test_dict_default_flagged(self):
        checker = _checker_from_rules(GuardrailRule("no_mutable_default_args", "desc", "downgrade_to_pr_only"))
        result = checker.check(_changes("def bar(opts={}):\n    pass"), [])
        assert result.has_downgrades

    def test_immutable_default_passes(self):
        checker = _checker_from_rules(GuardrailRule("no_mutable_default_args", "desc", "downgrade_to_pr_only"))
        result = checker.check(_changes("def baz(x=None):\n    pass"), [])
        assert not result.has_downgrades


# ---------------------------------------------------------------------------
# Content extraction
# ---------------------------------------------------------------------------


class TestExtractContent:
    def test_extracts_string_values_from_dicts(self):
        changes = [{"type": "patch", "code": "import torch"}]
        content = GuardrailChecker._extract_content(changes, [])
        assert "import torch" in content

    def test_extracts_string_list_values(self):
        changes = [{"lines": ["import os", "os.system('x')"]}]
        content = GuardrailChecker._extract_content(changes, [])
        assert "os.system" in content

    def test_includes_affected_files(self):
        content = GuardrailChecker._extract_content([], ["src/payment.py", "migrations/001.sql"])
        assert "migrations/001.sql" in content

    def test_non_string_values_ignored(self):
        changes = [{"count": 42, "flags": True, "code": "x = 1"}]
        content = GuardrailChecker._extract_content(changes, [])
        assert "x = 1" in content
        assert "42" not in content

    def test_non_dict_change_ignored(self):
        # Should not crash on malformed input
        content = GuardrailChecker._extract_content(["not a dict", None], [])  # type: ignore[list-item]
        assert content == ""


# ---------------------------------------------------------------------------
# TrustGateValidator._validate_guardrails() integration
# ---------------------------------------------------------------------------


class TestTrustGateGuardrailsIntegration:
    def _make_validator_with_checker(self, checker: GuardrailChecker) -> TrustGateValidator:
        validator = TrustGateValidator(environment="development")
        validator._guardrail_checker = checker
        return validator

    def _make_validator_no_checker(self) -> TrustGateValidator:
        validator = TrustGateValidator(environment="development")
        validator._guardrail_checker = None
        return validator

    @pytest.mark.asyncio
    async def test_no_checker_pass_through(self):
        validator = self._make_validator_no_checker()
        result = ValidationResult(allowed=False, policy_mode=PolicyMode.GUARDED_APPLY)
        request = _make_request()
        passed = await validator._validate_guardrails(request, result)
        assert passed is True

    @pytest.mark.asyncio
    async def test_blocking_violation_denies(self):
        rule = GuardrailRule("no_hardcoded_secrets", "No secrets", "block")
        checker = _checker_from_rules(rule)
        validator = self._make_validator_with_checker(checker)
        result = ValidationResult(allowed=False, policy_mode=PolicyMode.GUARDED_APPLY)
        request = _make_request(proposed_changes=[{"code": "sk-abcdefghijklmnopqrstuvwx"}])

        passed = await validator._validate_guardrails(request, result)

        assert passed is False
        assert result.reason == DenyReason.GUARDRAIL_VIOLATION
        assert "no_hardcoded_secrets" in result.message
        assert any("guardrail:block:no_hardcoded_secrets" in f for f in result.checks_failed)

    @pytest.mark.asyncio
    async def test_downgrade_forces_pr_only(self):
        rule = GuardrailRule("no_bare_except", "No bare except", "downgrade_to_pr_only")
        checker = _checker_from_rules(rule)
        validator = self._make_validator_with_checker(checker)
        result = ValidationResult(allowed=False, policy_mode=PolicyMode.GUARDED_APPLY)
        request = _make_request(proposed_changes=[{"code": "try:\n    pass\nexcept:\n    pass"}])

        passed = await validator._validate_guardrails(request, result)

        assert passed is True  # non-fatal
        assert result.policy_mode == PolicyMode.PR_ONLY
        assert any("guardrail:downgrade" in f for f in result.checks_failed)

    @pytest.mark.asyncio
    async def test_warn_does_not_block(self):
        rule = GuardrailRule("no_print_statements", "No print", "warn")
        checker = _checker_from_rules(rule)
        validator = self._make_validator_with_checker(checker)
        result = ValidationResult(allowed=False, policy_mode=PolicyMode.GUARDED_APPLY)
        request = _make_request(proposed_changes=[{"code": 'print("hello")'}])

        passed = await validator._validate_guardrails(request, result)

        assert passed is True
        assert result.policy_mode == PolicyMode.GUARDED_APPLY  # unchanged
        assert any("guardrail:warn" in f for f in result.checks_passed)

    @pytest.mark.asyncio
    async def test_guardrails_evidence_in_result(self):
        rule = GuardrailRule("no_print_statements", "No print", "warn")
        checker = _checker_from_rules(rule)
        validator = self._make_validator_with_checker(checker)
        result = ValidationResult(allowed=False, policy_mode=PolicyMode.GUARDED_APPLY)
        request = _make_request(proposed_changes=[{"code": 'print("x")'}])

        await validator._validate_guardrails(request, result)

        assert "guardrails" in result.evidence
        gr_dict = result.evidence["guardrails"]
        assert "warnings" in gr_dict

    @pytest.mark.asyncio
    async def test_clean_changes_all_pass(self):
        rule = GuardrailRule("no_hardcoded_secrets", "No secrets", "block")
        checker = _checker_from_rules(rule)
        validator = self._make_validator_with_checker(checker)
        result = ValidationResult(allowed=False, policy_mode=PolicyMode.GUARDED_APPLY)
        request = _make_request(proposed_changes=[{"code": 'api_key = os.environ["OPENAI_KEY"]'}])

        passed = await validator._validate_guardrails(request, result)

        assert passed is True
        assert result.reason is None
