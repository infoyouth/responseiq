"""
Watchdog Service — v2.18.0 #3 Post-Apply Monitoring + Auto-Rollback.

Monitors error rate in a configurable window after a ``guarded_apply``
and automatically triggers the rollback script if the threshold is breached.

State Machine:
    IDLE → MONITORING (started) → ROLLBACK_TRIGGERED | CLEAR (window elapsed)

Design Principles
-----------------
* The service is always feature-flagged via ``settings.watchdog_enabled``
  (default False) so teams opt-in explicitly.
* A ``metrics_callback`` hook lets callers plug in real metrics sources
  (DataDog, Prometheus) without coupling the service to specific SDKs.
* When no callback is provided, the service falls back to probing
  ``GET /health`` on the local server using ``aiohttp``.
* Every run (triggered or clear) writes a ``WatchdogRecord`` to the DB for
  audit purposes.

Trust Gate
----------
rationale    : Post-apply watchdog closes the "silent drift" risk — the SRE
               persona review identified no automated rollback after apply.
               This adds a safety net that activates within 5 min of a bad
               deploy and is fully reversible (just disable the flag).
blast_radius : Reads metrics/health endpoint; writes WatchdogRecord; on breach
               executes the pre-generated rollback script (same as manual
               ``python rollback_<id>.py``).
rollback_plan: Set ``RESPONSEIQ_WATCHDOG_ENABLED=false``; the service becomes
               a no-op immediately without code changes.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from responseiq.utils.logger import logger


# ---------------------------------------------------------------------------
# Config / Result data-classes
# ---------------------------------------------------------------------------


@dataclass
class WatchdogConfig:
    """Tunable parameters for a single watchdog monitoring session."""

    error_threshold: float = 0.05  # 5 % error rate triggers rollback
    window_seconds: int = 300  # 5-minute monitoring window
    poll_interval_seconds: int = 30  # How often to sample metrics
    health_url: str = "http://localhost:8000/health"  # Fallback health probe
    # Optional async callable: (incident_id: str) -> float  (error rate 0.0-1.0)
    metrics_callback: Optional[Callable[[str], Awaitable[float]]] = field(default=None, repr=False)


@dataclass
class WatchdogResult:
    """Outcome of a watchdog monitoring window."""

    incident_id: str
    triggered: bool  # True = threshold breached, rollback executed
    reason: str
    error_rate_observed: float  # Peak error rate seen during window
    error_threshold: float
    window_seconds: int
    rollback_script_path: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "triggered": self.triggered,
            "reason": self.reason,
            "error_rate_observed": round(self.error_rate_observed, 4),
            "error_threshold": self.error_threshold,
            "window_seconds": self.window_seconds,
            "rollback_script_path": self.rollback_script_path,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# ---------------------------------------------------------------------------
# Watchdog Service
# ---------------------------------------------------------------------------


class WatchdogService:
    """
    Post-apply error-rate monitor with automatic rollback trigger.

    Usage::

        svc = WatchdogService()
        result = await svc.monitor_post_apply(
            incident_id="INC-42",
            rollback_script_path=Path("rollbacks/rollback_INC-42.py"),
        )
    """

    def __init__(self) -> None:
        # In-flight sessions keyed by incident_id — status polling
        self._active: dict[str, WatchdogResult] = {}
        self._completed: dict[str, WatchdogResult] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def monitor_post_apply(
        self,
        incident_id: str,
        rollback_script_path: Optional[Path] = None,
        config: Optional[WatchdogConfig] = None,
    ) -> WatchdogResult:
        """
        Start monitoring and block until the window elapses or rollback fires.

        Args:
            incident_id:         Identifies the remediation being watched.
            rollback_script_path: Path to the ``rollback_<id>.py`` script.
                                  If absent, rollback is skipped (logged).
            config:               Tuning parameters; uses defaults if omitted.

        Returns:
            ``WatchdogResult`` describing whether rollback was triggered.
        """
        cfg = config or WatchdogConfig()
        result = WatchdogResult(
            incident_id=incident_id,
            triggered=False,
            reason="Monitoring window elapsed — no threshold breach.",
            error_rate_observed=0.0,
            error_threshold=cfg.error_threshold,
            window_seconds=cfg.window_seconds,
            rollback_script_path=str(rollback_script_path) if rollback_script_path else None,
        )
        self._active[incident_id] = result
        logger.info(
            f"👁️  Watchdog started for incident {incident_id} "
            f"(window={cfg.window_seconds}s, threshold={cfg.error_threshold:.0%})"
        )

        deadline = asyncio.get_event_loop().time() + cfg.window_seconds
        peak_rate = 0.0

        try:
            while asyncio.get_event_loop().time() < deadline:
                error_rate = await self._sample_error_rate(incident_id, cfg)
                peak_rate = max(peak_rate, error_rate)
                result.error_rate_observed = peak_rate

                if error_rate >= cfg.error_threshold:
                    logger.warning(
                        f"🚨 Watchdog BREACH: incident={incident_id} "
                        f"error_rate={error_rate:.1%} >= threshold={cfg.error_threshold:.1%}"
                    )
                    result.triggered = True
                    result.reason = (
                        f"Error rate {error_rate:.1%} exceeded threshold "
                        f"{cfg.error_threshold:.1%} — rollback triggered."
                    )
                    await self._execute_rollback(incident_id, rollback_script_path)
                    break

                await asyncio.sleep(cfg.poll_interval_seconds)
        finally:
            result.completed_at = datetime.now(timezone.utc)
            self._active.pop(incident_id, None)
            self._completed[incident_id] = result
            await self._persist_result(result)
            status = "TRIGGERED" if result.triggered else "CLEAR"
            logger.info(f"✅ Watchdog complete for {incident_id}: {status} (peak_rate={peak_rate:.1%})")

        return result

    def get_status(self, incident_id: str) -> Optional[WatchdogResult]:
        """Return the current or most-recent WatchdogResult for an incident."""
        return self._active.get(incident_id) or self._completed.get(incident_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _sample_error_rate(self, incident_id: str, cfg: WatchdogConfig) -> float:
        """Sample current error rate via callback or health probe fallback."""
        if cfg.metrics_callback is not None:
            try:
                rate = await cfg.metrics_callback(incident_id)
                return float(rate)
            except Exception as exc:
                logger.warning(f"Watchdog metrics_callback failed: {exc}; falling back to health probe")

        # Fallback: health endpoint probe — treat non-200 as 100% error rate
        try:
            import aiohttp  # type: ignore[import-untyped]

            async with aiohttp.ClientSession() as http:
                async with http.get(cfg.health_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    return 0.0 if resp.status == 200 else 1.0
        except Exception:
            # Can't reach health endpoint — treat as unhealthy
            return 1.0

    async def _execute_rollback(self, incident_id: str, script_path: Optional[Path]) -> None:
        """Execute the rollback Python script as a subprocess."""
        if script_path is None or not Path(script_path).exists():
            logger.warning(
                f"⚠️  Watchdog: rollback triggered for {incident_id} but "
                f"script not found at '{script_path}' — MANUAL INTERVENTION REQUIRED"
            )
            return

        logger.info(f"🔄 Watchdog: executing rollback script {script_path}")
        try:
            proc = await asyncio.create_subprocess_exec(
                "python",
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            if proc.returncode == 0:
                logger.info(f"✅ Watchdog rollback succeeded: {script_path}")
            else:
                logger.error(
                    f"❌ Watchdog rollback script exited {proc.returncode}",
                    stderr=stderr.decode("utf-8", errors="replace")[:500],
                )
        except asyncio.TimeoutError:
            logger.error(f"❌ Watchdog rollback timed out for {script_path}")
        except Exception as exc:
            logger.error(f"❌ Watchdog rollback execution failed: {exc}")

    async def _persist_result(self, result: WatchdogResult) -> None:
        """Write WatchdogRecord to DB; silently swallow errors."""
        try:
            from responseiq.db import get_session
            from responseiq.models.base import WatchdogRecord

            record = WatchdogRecord(
                incident_id=result.incident_id,
                triggered=result.triggered,
                reason=result.reason,
                error_rate_observed=result.error_rate_observed,
                error_threshold=result.error_threshold,
                window_seconds=result.window_seconds,
                rollback_script_path=result.rollback_script_path,
                started_at=result.started_at,
                completed_at=result.completed_at,
            )
            with next(get_session()) as session:  # type: ignore[call-arg]
                session.add(record)
                session.commit()
        except Exception as exc:
            logger.warning(f"⚠️  Watchdog: DB persist failed (non-fatal): {exc}")
