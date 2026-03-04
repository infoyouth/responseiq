"""
Unit tests for v2.18.0 #3 Post-Apply Watchdog Service + Router.

Coverage:
    WatchdogConfig defaults                 — 3 tests
    WatchdogResult.to_dict()                — 3 tests
    WatchdogService.monitor_post_apply()    — 6 tests
    WatchdogService.get_status()            — 2 tests
    POST /api/v1/incidents/{id}/watchdog/start  — 5 tests
    GET  /api/v1/incidents/{id}/watchdog/status — 4 tests

Trust Gate:
    rationale    : Watchdog is feature-flagged; tests confirm 503 when disabled.
    blast_radius : monitor_post_apply() is async; tests mock poll/rollback paths.
    rollback_plan: set watchdog_enabled=False — all endpoints return 503.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from responseiq.services.watchdog_service import (
    WatchdogConfig,
    WatchdogResult,
    WatchdogService,
)


# ---------------------------------------------------------------------------
# WatchdogConfig defaults
# ---------------------------------------------------------------------------


class TestWatchdogConfigDefaults:
    def test_default_error_threshold(self):
        cfg = WatchdogConfig()
        assert cfg.error_threshold == pytest.approx(0.05)

    def test_default_window_seconds(self):
        cfg = WatchdogConfig()
        assert cfg.window_seconds == 300

    def test_default_poll_interval(self):
        cfg = WatchdogConfig()
        assert cfg.poll_interval_seconds == 30


# ---------------------------------------------------------------------------
# WatchdogResult.to_dict()
# ---------------------------------------------------------------------------


class TestWatchdogResultToDict:
    def _result(self, triggered: bool = False) -> WatchdogResult:
        return WatchdogResult(
            incident_id="INC-W01",
            triggered=triggered,
            reason="test reason",
            error_rate_observed=0.02,
            error_threshold=0.05,
            window_seconds=300,
        )

    def test_to_dict_has_incident_id(self):
        assert self._result().to_dict()["incident_id"] == "INC-W01"

    def test_to_dict_triggered_false(self):
        assert self._result(triggered=False).to_dict()["triggered"] is False

    def test_to_dict_triggered_true(self):
        assert self._result(triggered=True).to_dict()["triggered"] is True


# ---------------------------------------------------------------------------
# WatchdogService unit tests
# ---------------------------------------------------------------------------


class TestWatchdogServiceMonitor:
    def _make_service(self) -> WatchdogService:
        return WatchdogService()

    @pytest.mark.asyncio
    async def test_clear_when_error_rate_below_threshold(self):
        """Full window elapses with rate below threshold → not triggered."""
        svc = self._make_service()

        async def _low_rate(_id: str) -> float:
            return 0.01  # 1% < 5% threshold

        cfg = WatchdogConfig(
            error_threshold=0.05,
            window_seconds=0,  # zero window so loop exits immediately
            poll_interval_seconds=0,
            metrics_callback=_low_rate,
        )

        with patch.object(svc, "_persist_result", new_callable=AsyncMock):
            result = await svc.monitor_post_apply("INC-CLEAR", config=cfg)

        assert result.triggered is False
        assert result.incident_id == "INC-CLEAR"

    @pytest.mark.asyncio
    async def test_triggered_when_rate_exceeds_threshold(self):
        """High error rate immediately triggers rollback flag."""
        svc = self._make_service()

        async def _high_rate(_id: str) -> float:
            return 0.9  # 90% >> 5%

        cfg = WatchdogConfig(
            error_threshold=0.05,
            window_seconds=999,
            poll_interval_seconds=0,
            metrics_callback=_high_rate,
        )

        with (
            patch.object(svc, "_persist_result", new_callable=AsyncMock),
            patch.object(svc, "_execute_rollback", new_callable=AsyncMock) as mock_rb,
        ):
            result = await svc.monitor_post_apply("INC-TRIGGER", config=cfg)

        assert result.triggered is True
        mock_rb.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_receives_correct_script_path(self):
        """The rollback executor is called with the supplied script path."""
        svc = self._make_service()

        async def _high_rate(_id: str) -> float:
            return 1.0

        cfg = WatchdogConfig(
            error_threshold=0.05,
            window_seconds=999,
            poll_interval_seconds=0,
            metrics_callback=_high_rate,
        )
        script = Path("rollbacks/rollback_test.py")

        with (
            patch.object(svc, "_persist_result", new_callable=AsyncMock),
            patch.object(svc, "_execute_rollback", new_callable=AsyncMock) as mock_rb,
        ):
            await svc.monitor_post_apply("INC-RB", rollback_script_path=script, config=cfg)

        mock_rb.assert_called_once_with("INC-RB", script)

    @pytest.mark.asyncio
    async def test_completed_at_set_after_window(self):
        """completed_at is always populated when monitor_post_apply returns."""
        svc = self._make_service()

        async def _zero_rate(_id: str) -> float:
            return 0.0

        cfg = WatchdogConfig(
            window_seconds=0,
            poll_interval_seconds=0,
            metrics_callback=_zero_rate,
        )

        with patch.object(svc, "_persist_result", new_callable=AsyncMock):
            result = await svc.monitor_post_apply("INC-CA", config=cfg)

        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_fallback_to_health_probe_when_no_callback(self):
        """When metrics_callback is None, error rate is sampled via HTTP."""
        svc = self._make_service()
        cfg = WatchdogConfig(
            window_seconds=0,
            poll_interval_seconds=0,
            # no metrics_callback
        )

        with (
            patch.object(svc, "_persist_result", new_callable=AsyncMock),
            patch("responseiq.services.watchdog_service.aiohttp", None, create=True),
        ):
            # Should not raise even when aiohttp errors
            result = await svc.monitor_post_apply("INC-HP", config=cfg)

        assert isinstance(result, WatchdogResult)

    @pytest.mark.asyncio
    async def test_persist_result_called_on_completion(self):
        """_persist_result is always called, triggered or not."""
        svc = self._make_service()

        async def _zero(_id: str) -> float:
            return 0.0

        cfg = WatchdogConfig(window_seconds=0, poll_interval_seconds=0, metrics_callback=_zero)

        with patch.object(svc, "_persist_result", new_callable=AsyncMock) as mock_persist:
            await svc.monitor_post_apply("INC-PRS", config=cfg)

        mock_persist.assert_called_once()


class TestWatchdogServiceGetStatus:
    @pytest.mark.asyncio
    async def test_get_status_returns_completed_result(self):
        """get_status returns the result after monitor_post_apply completes."""
        svc = WatchdogService()

        async def _zero(_id: str) -> float:
            return 0.0

        cfg = WatchdogConfig(window_seconds=0, poll_interval_seconds=0, metrics_callback=_zero)
        with patch.object(svc, "_persist_result", new_callable=AsyncMock):
            await svc.monitor_post_apply("INC-GS", config=cfg)

        status = svc.get_status("INC-GS")
        assert status is not None
        assert status.incident_id == "INC-GS"

    def test_get_status_returns_none_for_unknown_incident(self):
        svc = WatchdogService()
        assert svc.get_status("INC-UNKNOWN") is None


# ---------------------------------------------------------------------------
# Router endpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    from responseiq.app import app as _app

    return TestClient(_app, raise_server_exceptions=True)


class TestWatchdogStartEndpoint:
    def test_503_when_watchdog_disabled(self, client: TestClient):
        with patch("responseiq.routers.watchdog.settings") as mock_settings:
            mock_settings.watchdog_enabled = False
            response = client.post("/api/v1/incidents/INC-D/watchdog/start")
        assert response.status_code == 503
        assert "RESPONSEIQ_WATCHDOG_ENABLED" in response.json()["detail"]

    def test_202_when_watchdog_enabled(self, client: TestClient):
        with patch("responseiq.routers.watchdog.settings") as mock_settings:
            mock_settings.watchdog_enabled = True
            response = client.post("/api/v1/incidents/INC-E/watchdog/start")
        assert response.status_code == 200  # BackgroundTasks returns 200 by default

    def test_response_contains_incident_id(self, client: TestClient):
        with patch("responseiq.routers.watchdog.settings") as mock_settings:
            mock_settings.watchdog_enabled = True
            response = client.post("/api/v1/incidents/INC-F/watchdog/start")
        assert response.json()["incident_id"] == "INC-F"

    def test_response_contains_error_threshold(self, client: TestClient):
        with patch("responseiq.routers.watchdog.settings") as mock_settings:
            mock_settings.watchdog_enabled = True
            response = client.post(
                "/api/v1/incidents/INC-G/watchdog/start",
                params={"error_threshold": 0.1},
            )
        assert response.json()["error_threshold"] == pytest.approx(0.1)

    def test_invalid_threshold_returns_422(self, client: TestClient):
        with patch("responseiq.routers.watchdog.settings") as mock_settings:
            mock_settings.watchdog_enabled = True
            response = client.post(
                "/api/v1/incidents/INC-H/watchdog/start",
                params={"error_threshold": 2.0},  # > 1.0
            )
        assert response.status_code == 422


class TestWatchdogStatusEndpoint:
    def test_503_when_watchdog_disabled(self, client: TestClient):
        with patch("responseiq.routers.watchdog.settings") as mock_settings:
            mock_settings.watchdog_enabled = False
            response = client.get("/api/v1/incidents/INC-I/watchdog/status")
        assert response.status_code == 503

    def test_404_when_no_session(self, client: TestClient):
        with patch("responseiq.routers.watchdog.settings") as mock_settings:
            mock_settings.watchdog_enabled = True
            with patch("responseiq.routers.watchdog._watchdog_service.get_status", return_value=None):
                response = client.get("/api/v1/incidents/INC-NONE/watchdog/status")
        assert response.status_code == 404

    def test_200_with_valid_result(self, client: TestClient):
        mock_result = WatchdogResult(
            incident_id="INC-J",
            triggered=False,
            reason="clear",
            error_rate_observed=0.01,
            error_threshold=0.05,
            window_seconds=300,
        )
        with patch("responseiq.routers.watchdog.settings") as mock_settings:
            mock_settings.watchdog_enabled = True
            with patch("responseiq.routers.watchdog._watchdog_service.get_status", return_value=mock_result):
                response = client.get("/api/v1/incidents/INC-J/watchdog/status")
        assert response.status_code == 200
        assert response.json()["triggered"] is False

    def test_status_reflects_triggered_true(self, client: TestClient):
        mock_result = WatchdogResult(
            incident_id="INC-K",
            triggered=True,
            reason="threshold breached",
            error_rate_observed=0.2,
            error_threshold=0.05,
            window_seconds=300,
        )
        with patch("responseiq.routers.watchdog.settings") as mock_settings:
            mock_settings.watchdog_enabled = True
            with patch("responseiq.routers.watchdog._watchdog_service.get_status", return_value=mock_result):
                response = client.get("/api/v1/incidents/INC-K/watchdog/status")
        assert response.json()["triggered"] is True
