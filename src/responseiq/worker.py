"""
src/responseiq/worker.py

ARQ (Async Redis Queue) worker — durable background task execution.

Why ARQ over FastAPI BackgroundTasks
-------------------------------------
BackgroundTasks runs in the same process and is fire-and-forget with no
persistence, no retry, and no visibility.  If the server restarts mid-LLM
call, the job is silently lost.  ARQ gives:
  - Durability   — jobs survive server restarts (stored in Redis)
  - Retry        — configurable exponential back-off on failure
  - Visibility   — job status queryable via ARQ CLI (arq info)
  - Rate control — max_jobs limits concurrent LLM calls (respects API quotas)

Starting the worker
-------------------
    arq responseiq.worker.WorkerSettings

Or via Make target (added separately):
    uv run arq responseiq.worker.WorkerSettings

Configuration
-------------
    ARQ_REDIS_URL  — Redis DSN (default: redis://localhost:6379/0)
                     Set to empty/None to disable ARQ and fall back to
                     FastAPI BackgroundTasks.

Job functions are plain async functions that accept ``ctx: dict`` as the
first argument (ARQ convention).  They must be importable at worker startup.
"""

from __future__ import annotations

from typing import Any

from arq.connections import RedisSettings  # type: ignore[import-untyped]

from responseiq.config.settings import settings
from responseiq.services.incident_service import process_log_ingestion
from responseiq.utils.logger import logger


# ---------------------------------------------------------------------------
# Job functions
# ---------------------------------------------------------------------------


async def process_log_ingestion_job(ctx: dict, log_id: int) -> None:
    """
    ARQ job: analyse a persisted Log row and create an Incident.

    This is the durable counterpart of the in-process
    ``BackgroundTasks.add_task(process_log_ingestion, log_id)`` call.
    On failure ARQ will retry up to ``max_tries`` times with exponential
    back-off before marking the job as failed.
    """
    logger.info("ARQ job started: process_log_ingestion", log_id=log_id)
    process_log_ingestion(log_id)
    logger.info("ARQ job completed: process_log_ingestion", log_id=log_id)


# ---------------------------------------------------------------------------
# Worker settings
# ---------------------------------------------------------------------------


def _redis_settings_from_url(url: str) -> RedisSettings:
    """Parse a Redis DSN string into an ARQ RedisSettings object."""
    return RedisSettings.from_dsn(url)


def _get_redis_settings() -> RedisSettings:
    url = settings.arq_redis_url or "redis://localhost:6379/0"
    return _redis_settings_from_url(url)


class WorkerSettings:
    """
    ARQ worker configuration.

    Start with:  arq responseiq.worker.WorkerSettings
    """

    functions = [process_log_ingestion_job]

    # Limit concurrent jobs to avoid hammering the LLM API rate limits.
    max_jobs: int = 10

    # Retry up to 3 times with exponential back-off before marking failed.
    max_tries: int = 3

    @property
    def redis_settings(self) -> RedisSettings:  # type: ignore[override]
        return _get_redis_settings()


# ---------------------------------------------------------------------------
# Pool helper used by the FastAPI app at lifespan startup
# ---------------------------------------------------------------------------


async def create_arq_pool() -> Any:
    """
    Create and return an ARQ Redis pool.  Returns *None* gracefully when:
    - ``arq_redis_url`` is not configured, or
    - the ``arq`` package is not installed, or
    - Redis is unreachable (logs a warning; app continues without ARQ).
    """
    url = settings.arq_redis_url
    if not url:
        logger.debug("ARQ_REDIS_URL not set — background jobs will use FastAPI BackgroundTasks")
        return None

    try:
        from arq import create_pool  # type: ignore[import-untyped]

        pool = await create_pool(_redis_settings_from_url(url))
        logger.info("ARQ Redis pool connected", url=url.split("@")[-1])  # strip credentials
        return pool
    except ImportError:
        logger.warning("arq package not installed — falling back to BackgroundTasks")
        return None
    except Exception as exc:
        logger.warning(f"ARQ Redis connection failed: {exc} — falling back to BackgroundTasks")
        return None
