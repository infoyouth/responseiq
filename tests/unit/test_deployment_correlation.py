from datetime import datetime, timezone

from responseiq.schemas.deployment import DeploymentEvent, DeploymentEventKind
from responseiq.services.deployment_correlation_service import DeploymentCorrelationService


def _event(event_id: str, *, at: str, service: str = "payments", commit: str | None = None):
    return DeploymentEvent(
        event_id=event_id,
        kind=DeploymentEventKind.DEPLOYMENT,
        occurred_at=at,
        source="test-provider",
        service=service,
        commit_sha=commit,
    )


def test_event_normalizes_identity_and_naive_time():
    event = DeploymentEvent(
        event_id="deploy-1",
        kind="deployment",
        occurred_at=datetime(2026, 10, 2, 12),
        source="ci",
        service=" Payments ",
        commit_sha="ABCDEF",
    )
    assert event.service == "payments"
    assert event.commit_sha == "abcdef"
    assert event.occurred_at.tzinfo == timezone.utc


def test_correlation_weights_service_commit_and_temporal_proximity():
    service = DeploymentCorrelationService()
    incident_at = datetime.fromisoformat("2026-10-02T12:10:00+00:00")
    recent_match = _event("recent", at="2026-10-02T12:00:00Z", commit="abc123")
    older_match = _event("older", at="2026-10-02T06:00:00Z", commit="abc123")

    result = service.correlate(
        [older_match, recent_match],
        incident_at=incident_at,
        service="payments",
        commit_sha="ABC123",
    )

    assert result is not None
    assert result.event.event_id == "recent"
    assert result.relation == "correlated"
    assert {"service_match", "commit_sha_match", "within_lookback_window"} == set(result.reasons)


def test_temporal_proximity_alone_does_not_correlate():
    result = DeploymentCorrelationService().correlate(
        [_event("nearby", at="2026-10-02T12:09:00Z", service="inventory")],
        incident_at=datetime.fromisoformat("2026-10-02T12:10:00+00:00"),
        service="payments",
    )
    assert result is None


def test_configuration_and_feature_flag_evidence_are_scored():
    event = DeploymentEvent(
        event_id="config-change",
        kind=DeploymentEventKind.CONFIGURATION,
        occurred_at="2026-10-02T12:00:00Z",
        source="config-provider",
        service="payments",
        config_digest="sha256:feed",
        feature_flags={"new-checkout": "enabled"},
    )

    result = DeploymentCorrelationService().correlate(
        [event],
        incident_at=datetime.fromisoformat("2026-10-02T12:10:00+00:00"),
        service="payments",
        config_digest="SHA256:FEED",
        feature_flags={"new-checkout": "enabled"},
    )

    assert result is not None
    assert {"config_digest_match", "feature_flag_match"}.issubset(result.reasons)


def test_out_of_window_and_future_events_are_ignored():
    result = DeploymentCorrelationService().correlate(
        [
            _event("too-old", at="2026-10-01T00:00:00Z"),
            _event("future", at="2026-10-02T12:11:00Z"),
        ],
        incident_at=datetime.fromisoformat("2026-10-02T12:10:00+00:00"),
        service="payments",
    )
    assert result is None
