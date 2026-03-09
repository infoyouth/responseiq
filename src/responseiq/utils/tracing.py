# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Langfuse LLM tracing — optional, self-hostable.

Traces every LLM call (model, prompt, completion, token usage, latency)
so the eval flywheel can feed labelled data back into DSPy prompt
optimisation. Silently disabled when Langfuse credentials are absent
— no import errors, no crashes.
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
