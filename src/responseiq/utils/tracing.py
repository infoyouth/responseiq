"""
src/responseiq/utils/tracing.py

Langfuse LLM tracing — optional, self-hostable.

Langfuse traces every LLM call with: model name, prompt, completion,
token usage, latency, and a score once a human (or automated evaluator)
labels the output quality.  This powers the "eval flywheel" — the dataset
that feeds DSPy prompt optimisation in a later phase.

Configuration (all optional — tracing is silently disabled when absent):
    LANGFUSE_PUBLIC_KEY  — Langfuse project public key
    LANGFUSE_SECRET_KEY  — Langfuse project secret key
    LANGFUSE_HOST        — default: https://cloud.langfuse.com
                           set to your self-hosted URL for EU data residency

Usage:
    from responseiq.utils.tracing import get_langfuse, trace_generation

    lf = get_langfuse()
    if lf:
        gen = lf.generation(name="analyze_incident", model="gpt-4o", ...)
        gen.end(output=result)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from responseiq.utils.logger import logger

if TYPE_CHECKING:
    from langfuse import Langfuse  # type: ignore[import-untyped]

_langfuse_client: Optional["Langfuse"] = None
_langfuse_initialised = False


def get_langfuse() -> Optional["Langfuse"]:
    """
    Return a shared Langfuse client, or *None* if Langfuse is not configured.

    The client is initialised lazily on first call and cached for the lifetime
    of the process.  The function is safe to call from any async context —
    the Langfuse SDK itself is sync but thread-safe.
    """
    global _langfuse_client, _langfuse_initialised
    if _langfuse_initialised:
        return _langfuse_client

    _langfuse_initialised = True

    try:
        from langfuse import Langfuse  # type: ignore[import-untyped]

        from responseiq.config.settings import settings

        pub = settings.langfuse_public_key
        sec = settings.langfuse_secret_key

        if not pub or not sec:
            logger.debug("Langfuse not configured — LLM tracing disabled")
            return None

        kwargs: dict = {
            "public_key": pub,
            "secret_key": sec.get_secret_value() if hasattr(sec, "get_secret_value") else sec,
        }
        if settings.langfuse_host:
            kwargs["host"] = settings.langfuse_host

        _langfuse_client = Langfuse(**kwargs)
        logger.info("Langfuse LLM tracing enabled", host=settings.langfuse_host or "cloud.langfuse.com")

    except ImportError:
        logger.debug("langfuse package not installed — LLM tracing disabled")
    except Exception as exc:  # pragma: no cover
        logger.warning(f"Langfuse initialisation failed: {exc} — tracing disabled")

    return _langfuse_client


def flush_langfuse() -> None:
    """Flush any buffered Langfuse events.  Call from lifespan shutdown."""
    if _langfuse_client is not None:
        try:
            _langfuse_client.flush()
        except Exception as exc:  # pragma: no cover
            logger.debug("Langfuse flush error (non-fatal): %s", exc)


def score_langfuse(
    trace_name: str,
    score_name: str,
    value: float,
    comment: Optional[str] = None,
) -> None:
    """
    Create a Langfuse score labelling an LLM generation span (P-F1).

    Used by the feedback endpoint to label approved/rejected remediations.
    Links the score via ``comment`` which includes the trace_name
    (``log_{log_id}``).  Pass ``trace_id`` directly to ``create_score``
    when it becomes available from the generation span store.

    No-op when Langfuse is not configured or if the call fails.
    """
    lf = get_langfuse()
    if lf is None:
        return
    try:
        full_comment = f"trace:{trace_name}" + (f" | {comment}" if comment else "")
        lf.create_score(
            name=score_name,
            value=value,
            comment=full_comment,
        )
    except Exception as exc:  # pragma: no cover
        logger.debug("Langfuse score call failed (non-fatal): %s", exc)
