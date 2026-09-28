# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Post-apply watchdog monitoring router.

Exposes ``POST /api/v1/incidents/{id}/watchdog/start`` to kick off a
non-blocking background monitor after a ``guarded_apply``, and
``GET /api/v1/incidents/{id}/watchdog/status`` to check its state.
Auto-triggers the rollback script if the error rate breaches threshold.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from responseiq.config.settings import settings
from responseiq.services.watchdog_service import WatchdogConfig, WatchdogService
from responseiq.utils.logger import logger

router = APIRouter(prefix="/api/v1/incidents", tags=["Watchdog"])

# Module-level service instance — cheap, holds no DB connections at init
_watchdog_service = WatchdogService()


@router.post(
    "/{incident_id}/watchdog/start",
    summary="Start post-apply error-rate monitoring for an incident",
    responses={
        202: {"description": "Watchdog started; monitoring in background"},
        503: {"description": "Watchdog feature is disabled (RESPONSEIQ_WATCHDOG_ENABLED)"},
    },
)
async def start_watchdog(
    incident_id: str,
    background_tasks: BackgroundTasks,
    rollback_script: Optional[str] = Query(
        default=None,
        description="Path to the rollback_<id>.py script to run on breach",
    ),
    error_threshold: float = Query(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Error rate (0.0–1.0) that triggers rollback (default 5%)",
    ),
    window_seconds: int = Query(
        default=300,
        ge=30,
        le=3600,
        description="Monitoring window in seconds (default 300 = 5 min)",
    ),
    poll_interval_seconds: int = Query(
        default=30,
        ge=5,
        le=300,
        description="Sampling interval in seconds (default 30)",
    ),
):
    """
    Start a background watchdog for ``incident_id``.

    The watchdog polls the error rate every ``poll_interval_seconds`` for up to
    ``window_seconds``.  If ``error_threshold`` is breached, the pre-generated
    rollback script at ``rollback_script`` is executed.

    The call returns **immediately** with HTTP 202 — monitoring runs in the
    background.  Poll ``GET /watchdog/status`` to check progress.

    Args:
        incident_id:           String incident identifier.
        rollback_script:       Filesystem path to ``rollback_<id>.py``.
        error_threshold:       Fraction (0–1) that triggers rollback.
        window_seconds:        Total monitoring window.
        poll_interval_seconds: Sampling cadence.

    Raises:
        HTTPException 503: when ``watchdog_enabled`` setting is False.
    """
    if not settings.watchdog_enabled:
        raise HTTPException(
            status_code=503,
            detail=("Watchdog is disabled. Set RESPONSEIQ_WATCHDOG_ENABLED=true to enable post-apply monitoring."),
        )

    script_path = Path(rollback_script) if rollback_script else None
    config = WatchdogConfig(
        error_threshold=error_threshold,
        window_seconds=window_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )

    logger.info(
        f"📡 Watchdog start requested for incident {incident_id} "
        f"(threshold={error_threshold:.0%}, window={window_seconds}s)"
    )

    # Run monitor_post_apply as a fire-and-forget background task.
    # We wrap in asyncio.ensure_future so it launches on the running loop.
    background_tasks.add_task(
        _run_watchdog_bg,
        incident_id=incident_id,
        script_path=script_path,
        config=config,
    )

    return {
        "status": "started",
        "incident_id": incident_id,
        "error_threshold": error_threshold,
        "window_seconds": window_seconds,
        "poll_interval_seconds": poll_interval_seconds,
        "rollback_script": str(script_path) if script_path else None,
        "message": (
            f"Watchdog monitoring started for {incident_id}. "
            f"Will auto-rollback if error rate >= {error_threshold:.0%} "
            f"within {window_seconds}s window."
        ),
    }


@router.get(
    "/{incident_id}/watchdog/status",
    summary="Get current or most-recent watchdog status for an incident",
    responses={
        200: {"description": "Watchdog status (active or completed)"},
        404: {"description": "No watchdog session found for this incident"},
        503: {"description": "Watchdog feature is disabled"},
    },
)
def get_watchdog_status(incident_id: str):
    """
    Return the current or most-recent ``WatchdogResult`` for ``incident_id``.

    Reflects live state while the session is active, or the final state once
    the monitoring window has elapsed.

    Raises:
        HTTPException 404: no watchdog session found.
        HTTPException 503: watchdog feature is disabled.
    """
    if not settings.watchdog_enabled:
        raise HTTPException(
            status_code=503,
            detail="Watchdog is disabled. Set RESPONSEIQ_WATCHDOG_ENABLED=true.",
        )

    result = _watchdog_service.get_status(incident_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No watchdog session found for incident '{incident_id}'.",
        )
    return result.to_dict()


# ---------------------------------------------------------------------------
# Background task helper (must be a plain coroutine for BackgroundTasks)
# ---------------------------------------------------------------------------


async def _run_watchdog_bg(
    incident_id: str,
    script_path: Optional[Path],
    config: WatchdogConfig,
) -> None:
    """Background coroutine that drives WatchdogService.monitor_post_apply."""
    try:
        await _watchdog_service.monitor_post_apply(
            incident_id=incident_id,
            rollback_script_path=script_path,
            config=config,
        )
    except Exception as exc:
        logger.error(f"❌ Watchdog background task failed for {incident_id}: {exc}")
