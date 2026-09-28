"""Hermetic before/after regression checks for sandbox incident fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from fixture_runner import FixtureRunner, FixtureSpec


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTH_SOURCE = REPO_ROOT / "sandbox" / "services" / "auth_service.py"
AUTH_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "regressions" / "auth"
PAYMENT_SOURCE = REPO_ROOT / "sandbox" / "services" / "payment_service.py"
PAYMENT_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "regressions" / "payment"
INVENTORY_SOURCE = REPO_ROOT / "sandbox" / "services" / "inventory_service.py"
INVENTORY_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "regressions" / "inventory"

AUTH = FixtureRunner(FixtureSpec(AUTH_SOURCE, AUTH_FIXTURE))
PAYMENT = FixtureRunner(FixtureSpec(PAYMENT_SOURCE, PAYMENT_FIXTURE))
INVENTORY = FixtureRunner(FixtureSpec(INVENTORY_SOURCE, INVENTORY_FIXTURE))


def _run_auth_flow(runner: FixtureRunner, module_dir: Path):
    script = """
from auth_service import login, refresh_session

session = login("fixture@example.com", "password-hash")
refresh_session(session["access_token"], "fixture@example.com")
"""
    return runner.run(module_dir, script)


def _run_script(runner: FixtureRunner, module_dir: Path, script: str):
    return runner.run(module_dir, script)


@pytest.mark.parametrize("runner", [AUTH, PAYMENT, INVENTORY], ids=["auth", "payment", "inventory"])
def test_fixture_contract_metadata_is_complete(runner: FixtureRunner) -> None:
    expected = runner.spec.expected
    assert expected["affected_files"] == [runner.spec.source_path.name]
    assert expected["expected_failure"]
    assert expected["expected_success"]
    assert expected["policy_mode"] == "pr_only_until_validated"
    assert expected["evidence_level"] == "application_reproduction"


def test_auth_fixture_fails_before_patch_and_passes_after_patch(tmp_path: Path) -> None:
    """The fixture must prove an application-path failure and its correction."""
    expected = AUTH.spec.expected
    module_dir = AUTH.prepare(tmp_path)

    before = _run_auth_flow(AUTH, module_dir)
    assert before.returncode != 0
    assert expected["expected_failure"] in before.stderr

    fixed_dir = AUTH.prepare(tmp_path, patched=True, name="auth_fixed")

    after = _run_auth_flow(AUTH, fixed_dir)
    assert after.returncode == 0, after.stderr


def test_auth_fixture_rejects_patch_that_does_not_fix_refresh_failure(tmp_path: Path) -> None:
    expected = AUTH.spec.expected
    module_dir = AUTH.prepare(tmp_path, name="auth_wrong_patch")
    wrong_patch = (
        (AUTH_FIXTURE / "expected.patch")
        .read_text(encoding="utf-8")
        .replace('"last_seen": time.time()', '"unused": time.time()')
    )
    patch_path = tmp_path / "wrong.patch"
    patch_path.write_text(wrong_patch, encoding="utf-8")

    AUTH.run_command(["git", "apply", "--check", str(patch_path)], cwd=module_dir, check=True)
    AUTH.run_command(["git", "apply", str(patch_path)], cwd=module_dir, check=True)

    result = _run_auth_flow(AUTH, module_dir)
    assert result.returncode != 0
    assert expected["expected_failure"] in result.stderr


def test_payment_fixture_does_not_report_failed_charge_as_success(tmp_path: Path) -> None:
    """The payment fixture must preserve an upstream failure for its caller."""
    expected = PAYMENT.spec.expected
    buggy_dir = PAYMENT.prepare(tmp_path)
    script = """
import payment_service

def fail(_payload):
    raise payment_service.NetworkRetryExhausted("upstream unavailable")

payment_service._call_stripe = fail
result = payment_service.process_charge(100, "USD", "tok_fixture", "order-1")
assert result["status"] == "succeeded"
"""
    before = _run_script(PAYMENT, buggy_dir, script)
    assert before.returncode == 0, before.stderr

    fixed_dir = PAYMENT.prepare(tmp_path, patched=True, name="payment_fixed")
    after = _run_script(
        PAYMENT,
        fixed_dir,
        script.replace('assert result["status"] == "succeeded"', "raise AssertionError('swallowed')"),
    )
    assert after.returncode != 0
    assert expected["expected_failure"] in after.stderr


def test_inventory_fixture_releases_empty_result_connections(tmp_path: Path) -> None:
    """The inventory fixture must not exhaust its pool on empty results."""
    expected = INVENTORY.spec.expected
    script = """
import inventory_service

for _ in range(16):
    inventory_service.get_low_stock_items()
"""
    buggy_dir = INVENTORY.prepare(tmp_path)
    before = _run_script(INVENTORY, buggy_dir, script)
    assert before.returncode != 0
    assert expected["expected_failure"] in before.stderr

    fixed_dir = INVENTORY.prepare(tmp_path, patched=True, name="inventory_fixed")
    after = _run_script(INVENTORY, fixed_dir, script)
    assert after.returncode == 0, after.stderr
