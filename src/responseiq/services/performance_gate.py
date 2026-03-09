# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Performance regression gate.

Maintains an in-process rolling latency window per endpoint and compares
pre-fix vs post-fix samples to detect performance regressions after a
patch is applied. Emits OpenTelemetry span events so results appear in
Tempo/Jaeger automatically when a collector is configured.
"""

from __future__ import annotations

import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import AsyncIterator, Deque, Dict, List, Optional

from responseiq.utils.logger import logger

# ── defaults ──────────────────────────────────────────────────────────────────

#: How many samples to keep per endpoint in the rolling window.
DEFAULT_WINDOW_SIZE: int = 100

#: Regression threshold — 15% latency increase triggers a FAIL.
DEFAULT_REGRESSION_THRESHOLD: float = 1.15


# ── result schema ─────────────────────────────────────────────────────────────


@dataclass
class PerformanceGateResult:
    """Outcome of a single gate evaluation.

    Attributes:
        endpoint:            The named operation / HTTP path evaluated.
        baseline_p95_ms:     p95 latency of the baseline (pre-fix) sample set.
        post_fix_p95_ms:     p95 latency of the post-fix sample set.
        delta_pct:           % change: (post − baseline) / baseline × 100.
        threshold_pct:       Rejection threshold applied (default 15.0).
        passed:              False when post_fix_p95 > baseline_p95 × threshold.
        reason:              Human-readable verdict string.
        baseline_sample_n:   Number of baseline samples used.
        post_fix_sample_n:   Number of post-fix samples used.
        assessment_hash:     SHA-256 of (endpoint + baseline + post_fix + delta)
                             for ProofBundle forensic integrity.
    """

    endpoint: str
    baseline_p95_ms: float
    post_fix_p95_ms: float
    delta_pct: float
    threshold_pct: float
    passed: bool
    reason: str
    baseline_sample_n: int
    post_fix_sample_n: int
    assessment_hash: str = ""

    def __post_init__(self) -> None:
        if not self.assessment_hash:
            self.assessment_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        import hashlib

        payload = f"{self.endpoint}|{self.baseline_p95_ms:.4f}|{self.post_fix_p95_ms:.4f}|{self.delta_pct:.4f}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }


# ── insufficient data sentinel ────────────────────────────────────────────────


def _insufficient_data_result(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a passed=True result when there is not enough data to evaluate."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=True,  # no data → gate passes (benefit of the doubt)
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── p95 helper ────────────────────────────────────────────────────────────────


def _p95(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(0, int(len(sorted_s) * 0.95) - 1)
    return sorted_s[idx]


# ── gate ──────────────────────────────────────────────────────────────────────


@dataclass
class PerformanceGate:
    """Rolling-window latency gate with pre/post fix comparison.

    Thread-safe for use within a single Python process (asyncio eventloop).
    For multi-process deployments, back the store with Redis or a DB instead.
    """

    window_size: int = DEFAULT_WINDOW_SIZE
    regression_threshold: float = DEFAULT_REGRESSION_THRESHOLD

    # internal state
    _pre_fix: Dict[str, List[float]] = field(default_factory=dict)
    _post_fix: Dict[str, List[float]] = field(default_factory=dict)
    _rolling: Dict[str, Deque[float]] = field(default_factory=dict)
    _baseline_snapshot: Dict[str, float] = field(default_factory=dict)

    # ── recording ─────────────────────────────────────────────────────────────

    def record_pre_fix(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="pre_fix")

    def record_post_fix(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="post_fix")

    def record(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="rolling")

    def snapshot_baseline(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if not window:
            logger.warning("PerformanceGate: no rolling samples for '%s'; baseline not set", endpoint)
            return None
        baseline = _p95(window)
        self._baseline_snapshot[endpoint] = baseline
        logger.info(
            "PerformanceGate: baseline snapshotted",
            endpoint=endpoint,
            p95_ms=round(baseline, 3),
            n=len(window),
        )
        return baseline

    # ── evaluation ────────────────────────────────────────────────────────────

    def evaluate(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → pass with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is not None else self.regression_threshold
        threshold_pct = (thr - 1.0) * 100.0

        # Strategy 1: explicit pre/post samples
        pre_samples = self._pre_fix.get(endpoint, [])
        post_samples = self._post_fix.get(endpoint, [])

        if pre_samples and post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate passes (benefit of the doubt)
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    def baseline_p95(self, endpoint: str) -> Optional[float]:
        """Return the current baseline p95 for *endpoint*, or None."""
        return self._baseline_snapshot.get(endpoint) or (
            _p95(self._pre_fix[endpoint]) if self._pre_fix.get(endpoint) else None
        )

    # ── reset ─────────────────────────────────────────────────────────────────

    def reset(self, endpoint: Optional[str] = None) -> None:
        """Reset samples for *endpoint* (or ALL endpoints if None).

        Useful between tests and between remediation runs to avoid cross-run
        contamination.
        """
        if endpoint is None:
            self._pre_fix.clear()
            self._post_fix.clear()
            self._rolling.clear()
            self._baseline_snapshot.clear()
        else:
            self._pre_fix.pop(endpoint, None)
            self._post_fix.pop(endpoint, None)
            self._rolling.pop(endpoint, None)
            self._baseline_snapshot.pop(endpoint, None)

    # ── internal helpers ──────────────────────────────────────────────────────

    def _compare(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, post, thr, threshold_pct, len(pre_samples), len(post_samples))

    def _compare_snapshot(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, post, thr, threshold_pct, 0, len(rolling))

    def _build_result(
        self,
        endpoint: str,
        baseline: float,
        post: float,
        thr: float,
        threshold_pct: float,
        n_baseline: int,
        n_post: int,
    ) -> PerformanceGateResult:
        if baseline == 0.0:
            delta_pct = 0.0
            passed = True
            reason = "baseline_zero: gate passes"
        else:
            delta = (post - baseline) / baseline
            delta_pct = delta * 100.0
            passed = post <= baseline * thr
            if passed:
                reason = f"OK: +{delta_pct:.1f}% (threshold +{threshold_pct:.0f}%)"
            else:
                reason = (
                    f"REGRESSION: post_fix p95 {post:.1f}ms is "
                    f"{delta_pct:.1f}% above baseline {baseline:.1f}ms "
                    f"(threshold +{threshold_pct:.0f}%)"
                )

        result = PerformanceGateResult(
            endpoint=endpoint,
            baseline_p95_ms=round(baseline, 3),
            post_fix_p95_ms=round(post, 3),
            delta_pct=round(delta_pct, 2),
            threshold_pct=threshold_pct,
            passed=passed,
            reason=reason,
            baseline_sample_n=n_baseline,
            post_fix_sample_n=n_post,
        )

        level = "info" if passed else "warning"
        getattr(logger, level)(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    @staticmethod
    def _emit_otel_event(endpoint: str, duration_ms: float, phase: str) -> None:
        """Emit a span event to the active OTel span if one exists.

        No-op when no span is active (tests, batch CLI).
        """
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span and span.is_recording():
                span.add_event(
                    "perf_gate.sample",
                    {
                        "perf_gate.endpoint": endpoint,
                        "perf_gate.duration_ms": duration_ms,
                        "perf_gate.phase": phase,
                    },
                )
        except Exception:  # pragma: no cover  # noqa: S110 — never let OTel break the hot path
            pass


# ── async context manager ─────────────────────────────────────────────────────


@asynccontextmanager
async def measure_latency(
    perf_gate: PerformanceGate,
    endpoint: str,
    phase: str = "post_fix",
) -> AsyncIterator[None]:
    """Async context manager that measures wall-clock duration and records it.

    Args:
        perf_gate: The ``PerformanceGate`` instance to record into.
        endpoint:  Name of the operation being measured.
        phase:     ``"pre_fix"`` | ``"post_fix"`` | ``"rolling"``
                   Controls which recording method is called.

    Example::

        async with measure_latency(gate, "remediateIncident", phase="post_fix"):
            await my_async_operation()
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000.0
        if phase == "pre_fix":
            perf_gate.record_pre_fix(endpoint, duration_ms)
        elif phase == "post_fix":
            perf_gate.record_post_fix(endpoint, duration_ms)
        else:
            perf_gate.record(endpoint, duration_ms)


# ── module-level singleton ────────────────────────────────────────────────────

#: Global gate instance shared across the process.
#: Use ``gate.reset()`` in tests to prevent cross-test contamination.
gate = PerformanceGate()
