"""Hermetic before/after regression checks for sandbox incident fixtures."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTH_SOURCE = REPO_ROOT / "sandbox" / "services" / "auth_service.py"
AUTH_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "regressions" / "auth"
AUTH_PATCH = AUTH_FIXTURE / "expected.patch"
PAYMENT_SOURCE = REPO_ROOT / "sandbox" / "services" / "payment_service.py"
PAYMENT_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "regressions" / "payment"
INVENTORY_SOURCE = REPO_ROOT / "sandbox" / "services" / "inventory_service.py"
INVENTORY_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "regressions" / "inventory"


def _run_auth_flow(module_dir: Path) -> subprocess.CompletedProcess[str]:
    script = """
from auth_service import login, refresh_session

session = login("fixture@example.com", "password-hash")
refresh_session(session["access_token"], "fixture@example.com")
"""
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=module_dir,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def _prepare_fixture(tmp_path: Path, source: Path, fixture_dir: Path) -> Path:
    module_dir = tmp_path / fixture_dir.name
    module_dir.mkdir()
    (module_dir / source.name).write_bytes(source.read_bytes())
    subprocess.run(
        ["git", "apply", "--unidiff-zero", str(fixture_dir / "expected.patch")],
        cwd=module_dir,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return module_dir


def _run_script(module_dir: Path, script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=module_dir,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def test_auth_fixture_fails_before_patch_and_passes_after_patch(tmp_path: Path) -> None:
    """The fixture must prove an application-path failure and its correction."""
    expected = json.loads((AUTH_FIXTURE / "expected.json").read_text(encoding="utf-8"))
    module_dir = tmp_path / "auth_fixture"
    module_dir.mkdir()
    target = module_dir / "auth_service.py"
    target.write_bytes(AUTH_SOURCE.read_bytes())

    before = _run_auth_flow(module_dir)
    assert before.returncode != 0
    assert expected["expected_failure"] in before.stderr

    subprocess.run(
        ["git", "apply", str(AUTH_PATCH)],
        cwd=module_dir,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )

    after = _run_auth_flow(module_dir)
    assert after.returncode == 0, after.stderr


def test_payment_fixture_does_not_report_failed_charge_as_success(tmp_path: Path) -> None:
    """The payment fixture must preserve an upstream failure for its caller."""
    expected = json.loads((PAYMENT_FIXTURE / "expected.json").read_text(encoding="utf-8"))
    buggy_dir = tmp_path / "payment_buggy"
    buggy_dir.mkdir()
    (buggy_dir / PAYMENT_SOURCE.name).write_bytes(PAYMENT_SOURCE.read_bytes())
    script = """
import payment_service

def fail(_payload):
    raise payment_service.NetworkRetryExhausted("upstream unavailable")

payment_service._call_stripe = fail
result = payment_service.process_charge(100, "USD", "tok_fixture", "order-1")
assert result["status"] == "succeeded"
"""
    before = _run_script(buggy_dir, script)
    assert before.returncode == 0, before.stderr

    fixed_dir = _prepare_fixture(tmp_path, PAYMENT_SOURCE, PAYMENT_FIXTURE)
    after = _run_script(
        fixed_dir, script.replace('assert result["status"] == "succeeded"', "raise AssertionError('swallowed')")
    )
    assert after.returncode != 0
    assert expected["expected_failure"] in after.stderr


def test_inventory_fixture_releases_empty_result_connections(tmp_path: Path) -> None:
    """The inventory fixture must not exhaust its pool on empty results."""
    expected = json.loads((INVENTORY_FIXTURE / "expected.json").read_text(encoding="utf-8"))
    script = """
import inventory_service

for _ in range(16):
    inventory_service.get_low_stock_items()
"""
    buggy_dir = tmp_path / "inventory_buggy"
    buggy_dir.mkdir()
    (buggy_dir / INVENTORY_SOURCE.name).write_bytes(INVENTORY_SOURCE.read_bytes())
    before = _run_script(buggy_dir, script)
    assert before.returncode != 0
    assert expected["expected_failure"] in before.stderr

    fixed_dir = _prepare_fixture(tmp_path, INVENTORY_SOURCE, INVENTORY_FIXTURE)
    after = _run_script(fixed_dir, script)
    assert after.returncode == 0, after.stderr
