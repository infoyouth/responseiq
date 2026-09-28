from responseiq.utils.incident_fingerprint import incident_fingerprint, normalize_incident_log


def test_fingerprint_ignores_volatile_metadata():
    first = "2026-09-28T10:20:30Z ERROR request_id=req-123 database unavailable"
    second = "2026-09-28T11:45:00Z ERROR request_id=req-999 database unavailable"

    assert incident_fingerprint(first, service="payments") == incident_fingerprint(second, service="payments")


def test_fingerprint_changes_for_incident_signal_or_service():
    log = "ERROR database unavailable"

    assert incident_fingerprint(log, service="payments") != incident_fingerprint(
        "ERROR cache unavailable", service="payments"
    )
    assert incident_fingerprint(log, service="payments") != incident_fingerprint(log, service="orders")


def test_normalization_discards_blank_lines_and_collapses_whitespace():
    assert normalize_incident_log("  ERROR   database unavailable\n\n  ") == "error database unavailable"
