# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors

import asyncio

from responseiq.schemas.outcome import OutcomeSource, OutcomeStatus
from run_fixture_replay import replay_fixture_cases


def test_pinned_fixture_replays_emit_complete_synthetic_outcomes():
    entries = asyncio.run(replay_fixture_cases())

    assert len(entries) == 3
    assert {entry.source for entry in entries} == {OutcomeSource.SYNTHETIC_REPLAY}
    assert {entry.status for entry in entries} == {OutcomeStatus.FIXED}
    assert len({entry.dataset_revision for entry in entries}) == 1
    assert all(entry.dataset_revision.startswith("sha256:") for entry in entries)
    assert all(entry.repository_commit for entry in entries)
    assert all(entry.validation_passed is True for entry in entries)
    assert all(entry.root_cause_correct is None for entry in entries)
    assert {entry.case_id for entry in entries} == {
        "auth-refresh-missing-last-seen",
        "payment-upstream-error-swallowed",
        "inventory-empty-result-pool-leak",
    }
