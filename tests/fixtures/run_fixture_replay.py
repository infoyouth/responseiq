# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Replay pinned synthetic incidents in the bounded sandbox and emit JSONL outcomes."""

from __future__ import annotations

import asyncio
import hashlib
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from fixture_runner import FixtureRunner, FixtureSpec

from responseiq.schemas.outcome import OutcomeLedgerEntry, OutcomeSource, OutcomeStatus
from responseiq.services.sandbox_runner import SandboxRunner

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = Path(__file__).resolve().parent / "regressions"


@dataclass(frozen=True)
class ReplayCase:
    case_id: str
    source_path: Path
    fixture_dir: Path
    script: str


CASES = (
    ReplayCase(
        "auth-refresh-missing-last-seen",
        REPO_ROOT / "sandbox/services/auth_service.py",
        FIXTURE_ROOT / "auth",
        "from auth_service import login, refresh_session\n"
        "session = login('fixture@example.com', 'password-hash')\n"
        "refresh_session(session['access_token'], 'fixture@example.com')\n",
    ),
    ReplayCase(
        "payment-upstream-error-swallowed",
        REPO_ROOT / "sandbox/services/payment_service.py",
        FIXTURE_ROOT / "payment",
        "import payment_service\n"
        "def fail(_payload):\n"
        "    raise payment_service.NetworkRetryExhausted('upstream unavailable')\n"
        "payment_service._call_stripe = fail\n"
        "try:\n"
        "    payment_service.process_charge(100, 'USD', 'tok_fixture', 'order-1')\n"
        "except payment_service.NetworkRetryExhausted:\n"
        "    pass\n"
        "else:\n"
        "    raise AssertionError('NetworkRetryExhausted was swallowed')\n",
    ),
    ReplayCase(
        "inventory-empty-result-pool-leak",
        REPO_ROOT / "sandbox/services/inventory_service.py",
        FIXTURE_ROOT / "inventory",
        "import inventory_service\nfor _ in range(16):\n    inventory_service.get_low_stock_items()\n",
    ),
)


def _dataset_revision() -> str:
    digest = hashlib.sha256()
    for case in CASES:
        for path in (case.source_path, case.fixture_dir / "expected.json", case.fixture_dir / "expected.patch"):
            digest.update(path.relative_to(REPO_ROOT).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
        digest.update(case.script.encode("utf-8"))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _repository_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


async def replay_fixture_cases() -> list[OutcomeLedgerEntry]:
    sandbox = SandboxRunner()
    dataset_revision = _dataset_revision()
    repository_commit = _repository_commit()
    entries: list[OutcomeLedgerEntry] = []

    for case in CASES:
        expected = FixtureSpec(case.source_path, case.fixture_dir).expected
        expected_failure = str(expected["expected_failure"])
        fixture = FixtureRunner(FixtureSpec(case.source_path, case.fixture_dir))
        started_at = time.monotonic()

        with tempfile.TemporaryDirectory(prefix=f"responseiq-replay-{case.case_id}-") as temporary:
            temporary_path = Path(temporary)
            before_path = fixture.prepare(temporary_path, name="before")
            before = await sandbox.run([sys.executable, "-c", case.script], cwd=before_path)
            before_output = before.output.decode("utf-8", errors="replace")
            baseline_reproduced = before.returncode != 0 and expected_failure in before_output

            after_path = fixture.prepare(temporary_path, patched=True, name="after")
            after = await sandbox.run([sys.executable, "-c", case.script], cwd=after_path)
            validation_passed = after.returncode == 0 and not after.timed_out
            replay_passed = baseline_reproduced and validation_passed

        entries.append(
            OutcomeLedgerEntry(
                incident_id=f"synthetic:{case.case_id}",
                source=OutcomeSource.SYNTHETIC_REPLAY,
                status=OutcomeStatus.FIXED if replay_passed else OutcomeStatus.FAILED,
                dataset_name="responseiq-pinned-fixture-replays",
                dataset_revision=dataset_revision,
                case_id=case.case_id,
                repository_commit=repository_commit,
                patch_applied=True,
                validation_passed=validation_passed,
                duration_ms=(time.monotonic() - started_at) * 1000,
                evidence_level="application_reproduction" if replay_passed else None,
                evidence_completeness=1.0 if baseline_reproduced and validation_passed else 0.5,
            )
        )

    return entries


def main() -> int:
    entries = asyncio.run(replay_fixture_cases())
    for entry in entries:
        print(entry.model_dump_json())
    return 0 if all(entry.status == OutcomeStatus.FIXED for entry in entries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
