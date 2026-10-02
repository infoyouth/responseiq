"""Correlate normalized deployment events with an incident timeline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

from responseiq.schemas.deployment import DeploymentCorrelationResult, DeploymentEvent


class DeploymentCorrelationService:
    """Rank recent events using identity and temporal evidence, never infer cause."""

    def correlate(
        self,
        events: Iterable[DeploymentEvent],
        *,
        incident_at: datetime,
        service: str | None = None,
        commit_sha: str | None = None,
        image_sha: str | None = None,
        config_digest: str | None = None,
        feature_flags: dict[str, str] | None = None,
        lookback_hours: int = 24,
    ) -> DeploymentCorrelationResult | None:
        if lookback_hours <= 0:
            raise ValueError("lookback_hours must be positive")

        incident_time = _as_utc(incident_at)
        normalized_service = service.strip().lower() if service else None
        normalized_commit = commit_sha.strip().lower() if commit_sha else None
        normalized_image = image_sha.strip().lower() if image_sha else None
        normalized_config = config_digest.strip().lower() if config_digest else None
        normalized_flags = {key.strip(): value.strip() for key, value in (feature_flags or {}).items()}
        earliest = incident_time - timedelta(hours=lookback_hours)

        candidates: list[tuple[float, datetime, str, DeploymentCorrelationResult]] = []
        for event in events:
            event_time = _as_utc(event.occurred_at)
            if event_time < earliest or event_time > incident_time:
                continue

            reasons: list[str] = []
            score = 0.0
            if normalized_service and event.service == normalized_service:
                score += 0.30
                reasons.append("service_match")
            if normalized_commit and event.commit_sha == normalized_commit:
                score += 0.40
                reasons.append("commit_sha_match")
            if normalized_image and event.image_sha == normalized_image:
                score += 0.40
                reasons.append("image_sha_match")
            if normalized_config and event.config_digest == normalized_config:
                score += 0.35
                reasons.append("config_digest_match")
            matching_flags = {key for key, value in normalized_flags.items() if event.feature_flags.get(key) == value}
            if matching_flags:
                score += min(0.35, 0.15 * len(matching_flags))
                reasons.append("feature_flag_match")

            # Time proximity adds context, but cannot qualify an event by itself.
            age_ratio = (incident_time - event_time).total_seconds() / (lookback_hours * 3600)
            score += 0.20 * max(0.0, 1.0 - age_ratio)
            reasons.append("within_lookback_window")
            if not any(reason.endswith("_match") for reason in reasons):
                continue

            confidence = min(score / 1.65, 0.95)
            result = DeploymentCorrelationResult(
                event=event,
                confidence=round(confidence, 3),
                reasons=reasons,
                lookback_hours=lookback_hours,
            )
            candidates.append((confidence, event_time, event.event_id, result))

        if not candidates:
            return None
        return max(candidates, key=lambda candidate: (candidate[0], candidate[1], candidate[2]))[3]


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
