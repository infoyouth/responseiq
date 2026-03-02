"""
src/responseiq/temporal/worker.py

Temporal Worker bootstrap for ResponseIQ (P-F4).

The worker is started as a background task in the FastAPI lifespan when
``settings.temporal_enabled = True`` AND the ``temporalio`` package is
installed. It is completely inert otherwise — the function returns ``None``
immediately so the rest of the application boots without a Temporal server.

Usage
─────
Called from app.py lifespan:

    if settings.temporal_enabled:
        from responseiq.temporal.worker import start_temporal_worker
        app.state.temporal_worker = await start_temporal_worker()

The returned handle is stored in ``app.state.temporal_worker`` so the lifespan
shutdown block can call ``await app.state.temporal_worker.shutdown()`` cleanly.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from responseiq.temporal import TEMPORAL_AVAILABLE

if TYPE_CHECKING:
    pass  # type stubs only — keep this module importable without temporalio

logger = logging.getLogger(__name__)


async def get_temporal_client():  # type: ignore[return]
    """
    Build and return a connected ``temporalio.client.Client``.

    Returns ``None`` when ``temporalio`` is not installed or Temporal server is
    unreachable — callers must guard: ``if client is None: return None``.
    """
    if not TEMPORAL_AVAILABLE:
        return None

    try:
        from temporalio.client import Client  # type: ignore[import-untyped]

        from responseiq.config.settings import settings

        client = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
        )
        logger.info(
            "Connected to Temporal server",
            extra={"host": settings.temporal_host, "namespace": settings.temporal_namespace},
        )
        return client
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not connect to Temporal server: %s", exc)
        return None


async def start_temporal_worker() -> Optional[asyncio.Task]:  # type: ignore[return]
    """
    Start the Temporal worker in a background asyncio task.

    Returns
    -------
    asyncio.Task | None
        The running worker task, or ``None`` if Temporal is disabled / unavailable.
        ``None`` return is safe — the caller (lifespan) stores it in app.state.

    Activites registered
    --------------------
    All activities from ``responseiq.temporal.activities.ALL_ACTIVITIES``.

    Workflow registered
    ------------------
    ``responseiq.temporal.workflows.RemediationWorkflow``
    """
    from responseiq.config.settings import settings

    if not settings.temporal_enabled:
        logger.debug("Temporal worker disabled (TEMPORAL_ENABLED=false). Skipping startup.")
        return None

    if not TEMPORAL_AVAILABLE:
        logger.warning(
            "TEMPORAL_ENABLED=true but `temporalio` is not installed. Install with:  pip install 'responseiq[temporal]'"
        )
        return None

    client = await get_temporal_client()
    if client is None:
        return None

    try:
        from temporalio.worker import Worker  # type: ignore[import-untyped]

        from responseiq.temporal.activities import ALL_ACTIVITIES
        from responseiq.temporal.workflows import RemediationWorkflow

        worker = Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[RemediationWorkflow],
            activities=ALL_ACTIVITIES,
        )

        task: asyncio.Task = asyncio.create_task(
            worker.run(),
            name="temporal-worker",
        )

        logger.info(
            "Temporal worker started",
            extra={
                "task_queue": settings.temporal_task_queue,
                "namespace": settings.temporal_namespace,
                "workflows": ["RemediationWorkflow"],
                "activities": [a.__name__ for a in ALL_ACTIVITIES],
            },
        )
        return task

    except Exception as exc:  # pragma: no cover
        logger.error("Failed to start Temporal worker: %s", exc)
        return None
