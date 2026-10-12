# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors

from unittest.mock import patch

from responseiq.schemas.outcome import OutcomeLedgerEntry, OutcomeSource, OutcomeStatus
from responseiq.services.audit_service import AuditEventType
from responseiq.services.outcome_ledger_service import record_outcome


def test_record_outcome_persists_structured_provenance_and_metrics():
    entry = OutcomeLedgerEntry(
        incident_id="incident-42",
        source=OutcomeSource.SYNTHETIC_REPLAY,
        status=OutcomeStatus.FIXED,
        dataset_name="responseiq-replay",
        dataset_revision="sha256:fixture-set-v3",
        case_id="payments-timeout-01",
        repository_commit="0123456789abcdef0123456789abcdef01234567",
        validation_passed=True,
        evidence_completeness=0.9,
    )

    with patch("responseiq.services.outcome_ledger_service.log_event_sync", return_value=object()) as log_event:
        assert record_outcome(entry) is True

    event_type, action = log_event.call_args.args
    metadata = log_event.call_args.kwargs["metadata"]
    assert event_type == AuditEventType.REMEDIATION_OUTCOME_RECORDED
    assert "fixed" in action
    assert metadata["source"] == "synthetic_replay"
    assert metadata["dataset_revision"] == "sha256:fixture-set-v3"
    assert metadata["repository_commit"] == "0123456789abcdef0123456789abcdef01234567"
    assert metadata["validation_passed"] is True
    assert metadata["root_cause_correct"] is None


def test_record_outcome_fails_when_audit_store_is_unavailable():
    entry = OutcomeLedgerEntry(
        incident_id="incident-43",
        source=OutcomeSource.HUMAN_REVIEW,
        status=OutcomeStatus.REJECTED,
    )

    with patch("responseiq.services.outcome_ledger_service.log_event_sync", return_value=None):
        assert record_outcome(entry) is False
