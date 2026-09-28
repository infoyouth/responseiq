"""
src/responseiq/temporal/__init__.py

Temporal durable workflow scaffolding (P-F4).

FEATURE FLAG
────────────
    TEMPORAL_ENABLED=false  (default)

Nothing runs until TEMPORAL_ENABLED=true AND a Temporal server is reachable
at TEMPORAL_HOST (default: localhost:7233).

Activate when:
  • Any remediation workflow regularly exceeds 30 minutes wall time, OR
  • A "Wait for Human Approval" gate must survive process restarts.

Until then, ARQ handles all background jobs correctly.

Checking availability
─────────────────────
    from responseiq.temporal import TEMPORAL_AVAILABLE

    if TEMPORAL_AVAILABLE:
        # temporalio is installed; safe to import workflows/activities
"""

from __future__ import annotations

try:
    import temporalio  # noqa: F401  # type: ignore[import-untyped]

    TEMPORAL_AVAILABLE = True
except ImportError:
    TEMPORAL_AVAILABLE = False

__all__ = ["TEMPORAL_AVAILABLE"]
