"""tests/unit/test_performance_gate.py

P5 Performance Gate — comprehensive unit tests.

Coverage targets
────────────────
- _p95() math (empty, single, even, odd, 100-sample)
- PerformanceGate.record_pre_fix / record_post_fix / record
- PerformanceGate.evaluate() — pass (no regression)
- PerformanceGate.evaluate() — fail (regression > 15%)
- PerformanceGate.evaluate() — exact at threshold (pass boundary)
- PerformanceGate.evaluate() — insufficient data sentinel (benefit-of-doubt)
- PerformanceGate.evaluate() — baseline zero guard
- PerformanceGate.snapshot_baseline() → Strategy 2
- PerformanceGate.reset() — single endpoint + all-endpoints
- PerformanceGate.baseline_p95() helper
- measure_latency async context manager — duration recorded, phase routing
- PerformanceGateResult.assessment_hash — SHA-256 reproducibility + mutation
- PerformanceGateResult.to_dict() — serialisation round-trip
- ProofBundle.perf_gate_result field integration
- Module-level singleton `gate` is a PerformanceGate
"""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import datetime, timezone
from typing import List

import pytest

from responseiq.schemas.proof import ProofBundle
from responseiq.services.performance_gate import (
    DEFAULT_REGRESSION_THRESHOLD,
    PerformanceGate,
    PerformanceGateResult,
    _p95,
    gate,
    measure_latency,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _fresh() -> PerformanceGate:
    """Return a clean PerformanceGate for each test."""
    g = PerformanceGate()
    return g


EP = "test_endpoint"


# ─────────────────────────────────────────────────────────────────────────────
# _p95() math
# ─────────────────────────────────────────────────────────────────────────────


class TestP95:
    def test_empty_returns_zero(self):
        assert _p95([]) == 0.0

    def test_single_element(self):
        assert _p95([42.0]) == 42.0

    def test_two_elements(self):
        # nearest-rank: idx = max(0, int(2 * 0.95) - 1) = max(0,0) = 0 → sorted[0]
        assert _p95([10.0, 20.0]) == 10.0

    def test_sorted_order_is_applied(self):
        # Unsorted input — p95 of [1..10] idx = max(0, int(10*0.95)-1) = 8 → 9.0
        samples = [float(i) for i in range(10, 0, -1)]  # [10,9,...,1]
        assert _p95(samples) == _p95(sorted(samples))

    def test_100_samples_p95_is_95th(self):
        samples = [float(i) for i in range(1, 101)]  # 1…100
        # idx = max(0, int(100 * 0.95) - 1) = 94 → sorted[94] = 95.0
        assert _p95(samples) == 95.0

    def test_uniform_samples(self):
        assert _p95([100.0] * 50) == 100.0


# ─────────────────────────────────────────────────────────────────────────────
# PerformanceGate — recording
# ─────────────────────────────────────────────────────────────────────────────


class TestRecording:
    def test_record_pre_fix_stores_samples(self):
        g = _fresh()
        g.record_pre_fix(EP, 50.0)
        g.record_pre_fix(EP, 60.0)
        assert g._pre_fix[EP] == [50.0, 60.0]

    def test_record_post_fix_stores_samples(self):
        g = _fresh()
        g.record_post_fix(EP, 55.0)
        assert g._post_fix[EP] == [55.0]

    def test_record_rolling_uses_deque(self):
        g = PerformanceGate(window_size=3)
        for v in [10.0, 20.0, 30.0, 40.0]:
            g.record(EP, v)
        assert list(g._rolling[EP]) == [20.0, 30.0, 40.0]  # oldest evicted

    def test_record_does_not_contaminate_pre_post(self):
        g = _fresh()
        g.record(EP, 100.0)
        assert EP not in g._pre_fix
        assert EP not in g._post_fix


# ─────────────────────────────────────────────────────────────────────────────
# PerformanceGate — evaluate() Strategy 1 (pre/post samples)
# ─────────────────────────────────────────────────────────────────────────────


class TestEvaluatePrePost:
    def _setup(self, pre: List[float], post: List[float]) -> tuple[PerformanceGate, PerformanceGateResult]:
        g = _fresh()
        for v in pre:
            g.record_pre_fix(EP, v)
        for v in post:
            g.record_post_fix(EP, v)
        return g, g.evaluate(EP)

    def test_pass_when_no_regression(self):
        _, result = self._setup([100.0] * 10, [105.0] * 10)
        assert result.passed is True
        assert "OK" in result.reason

    def test_fail_when_regression_exceeds_threshold(self):
        # 100 ms baseline → post 120 ms (20% above, threshold = 15%)
        _, result = self._setup([100.0] * 10, [120.0] * 10)
        assert result.passed is False
        assert "REGRESSION" in result.reason

    def test_pass_at_exact_threshold_boundary(self):
        # 14.9% increase (just under the 15% threshold) → must pass
        _, result = self._setup([100.0] * 10, [114.9] * 10)
        assert result.passed is True

    def test_fail_just_above_threshold(self):
        # 100 ms × 1.151 = 115.1 ms → fail
        _, result = self._setup([100.0] * 10, [115.1] * 10)
        assert result.passed is False

    def test_delta_pct_is_accurate(self):
        _, result = self._setup([100.0] * 10, [120.0] * 10)
        assert abs(result.delta_pct - 20.0) < 0.1

    def test_sample_counts_populated(self):
        _, result = self._setup([100.0] * 5, [110.0] * 7)
        assert result.baseline_sample_n == 5
        assert result.post_fix_sample_n == 7

    def test_custom_threshold_override(self):
        g = _fresh()
        for _ in range(5):
            g.record_pre_fix(EP, 100.0)
            g.record_post_fix(EP, 108.0)  # 8% above baseline
        # Default 15% → pass; custom 5% → fail
        assert g.evaluate(EP).passed is True
        assert g.evaluate(EP, threshold=1.05).passed is False


# ─────────────────────────────────────────────────────────────────────────────
# PerformanceGate — evaluate() Strategy 2 (snapshot baseline + rolling)
# ─────────────────────────────────────────────────────────────────────────────


class TestEvaluateSnapshotRolling:
    def test_pass_strategy_2(self):
        g = _fresh()
        for v in [100.0] * 5:
            g.record(EP, v)
        g.snapshot_baseline(EP)
        for v in [105.0] * 5:
            g.record(EP, v)
        result = g.evaluate(EP)
        assert result.passed is True

    def test_fail_strategy_2(self):
        g = _fresh()
        for v in [100.0] * 5:
            g.record(EP, v)
        g.snapshot_baseline(EP)
        for v in [130.0] * 5:
            g.record(EP, v)
        result = g.evaluate(EP)
        assert result.passed is False

    def test_snapshot_returns_p95_value(self):
        g = _fresh()
        for v in [100.0] * 20:
            g.record(EP, v)
        p95 = g.snapshot_baseline(EP)
        assert p95 == 100.0

    def test_snapshot_none_when_no_rolling_samples(self):
        g = _fresh()
        result = g.snapshot_baseline(EP)
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# PerformanceGate — evaluate() Strategy 3 (insufficient data)
# ─────────────────────────────────────────────────────────────────────────────


class TestEvaluateInsufficientData:
    def test_passes_with_no_data(self):
        g = _fresh()
        result = g.evaluate("brand_new_endpoint")
        assert result.passed is True
        assert "insufficient_data" in result.reason

    def test_passes_with_only_pre_fix(self):
        g = _fresh()
        g.record_pre_fix(EP, 100.0)
        result = g.evaluate(EP)
        assert result.passed is True  # no post_fix yet

    def test_passes_with_only_post_fix(self):
        g = _fresh()
        g.record_post_fix(EP, 100.0)
        result = g.evaluate(EP)
        assert result.passed is True  # no pre_fix

    def test_zero_baseline_guard(self):
        """Evaluating when baseline resolves to 0.0 should not divide by zero."""
        g = _fresh()
        g.record_pre_fix(EP, 0.0)
        g.record_post_fix(EP, 50.0)
        result = g.evaluate(EP)
        assert result.passed is True
        assert result.delta_pct == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# PerformanceGate — reset()
# ─────────────────────────────────────────────────────────────────────────────


class TestReset:
    def test_reset_single_endpoint(self):
        g = _fresh()
        g.record_pre_fix(EP, 100.0)
        g.record_post_fix(EP, 110.0)
        g.record(EP, 105.0)
        g.snapshot_baseline(EP)
        g.reset(EP)
        assert EP not in g._pre_fix
        assert EP not in g._post_fix
        assert EP not in g._rolling
        assert EP not in g._baseline_snapshot

    def test_reset_all_endpoints(self):
        g = _fresh()
        for ep in ["ep1", "ep2", "ep3"]:
            g.record(ep, 50.0)
        g.reset()
        assert not g._rolling

    def test_reset_does_not_affect_other_endpoint(self):
        g = _fresh()
        g.record(EP, 100.0)
        g.record("other", 200.0)
        g.reset(EP)
        assert "other" in g._rolling


# ─────────────────────────────────────────────────────────────────────────────
# PerformanceGate — baseline_p95() helper
# ─────────────────────────────────────────────────────────────────────────────


class TestBaselineP95Helper:
    def test_returns_snapshot_if_available(self):
        g = _fresh()
        for v in [100.0] * 5:
            g.record(EP, v)
        g.snapshot_baseline(EP)
        assert g.baseline_p95(EP) == 100.0

    def test_returns_pre_fix_p95_if_no_snapshot(self):
        g = _fresh()
        for v in [80.0] * 10:
            g.record_pre_fix(EP, v)
        assert g.baseline_p95(EP) == 80.0

    def test_returns_none_when_no_data(self):
        g = _fresh()
        assert g.baseline_p95(EP) is None


# ─────────────────────────────────────────────────────────────────────────────
# measure_latency async context manager
# ─────────────────────────────────────────────────────────────────────────────


class TestMeasureLatency:
    @pytest.mark.asyncio
    async def test_records_duration_rolling(self):
        g = _fresh()
        async with measure_latency(g, EP, phase="rolling"):
            await asyncio.sleep(0.01)
        assert len(g._rolling[EP]) == 1
        assert g._rolling[EP][0] >= 10.0  # ≥ 10 ms sleep

    @pytest.mark.asyncio
    async def test_records_pre_fix_phase(self):
        g = _fresh()
        async with measure_latency(g, EP, phase="pre_fix"):
            await asyncio.sleep(0)
        assert len(g._pre_fix.get(EP, [])) == 1

    @pytest.mark.asyncio
    async def test_records_post_fix_phase(self):
        g = _fresh()
        async with measure_latency(g, EP, phase="post_fix"):
            await asyncio.sleep(0)
        assert len(g._post_fix.get(EP, [])) == 1

    @pytest.mark.asyncio
    async def test_records_even_on_exception(self):
        """Duration must be recorded even when the body raises."""
        g = _fresh()
        with pytest.raises(ValueError):
            async with measure_latency(g, EP, phase="rolling"):
                raise ValueError("boom")
        assert len(g._rolling[EP]) == 1

    @pytest.mark.asyncio
    async def test_default_phase_is_post_fix(self):
        g = _fresh()
        async with measure_latency(g, EP):  # default phase
            pass
        assert g._post_fix.get(EP)


# ─────────────────────────────────────────────────────────────────────────────
# PerformanceGateResult — hash and serialisation
# ─────────────────────────────────────────────────────────────────────────────


class TestPerformanceGateResult:
    def _result(self, **kwargs) -> PerformanceGateResult:
        defaults = dict(
            endpoint=EP,
            baseline_p95_ms=100.0,
            post_fix_p95_ms=105.0,
            delta_pct=5.0,
            threshold_pct=15.0,
            passed=True,
            reason="OK: +5.0% (threshold +15%)",
            baseline_sample_n=10,
            post_fix_sample_n=10,
        )
        defaults.update(kwargs)
        return PerformanceGateResult(**defaults)

    def test_assessment_hash_is_sha256(self):
        r = self._result()
        payload = f"{r.endpoint}|{r.baseline_p95_ms:.4f}|{r.post_fix_p95_ms:.4f}|{r.delta_pct:.4f}"
        expected = hashlib.sha256(payload.encode()).hexdigest()
        assert r.assessment_hash == expected

    def test_assessment_hash_is_stable(self):
        r1 = self._result()
        r2 = self._result()
        assert r1.assessment_hash == r2.assessment_hash

    def test_assessment_hash_changes_with_different_values(self):
        r1 = self._result(post_fix_p95_ms=105.0)
        r2 = self._result(post_fix_p95_ms=120.0)
        assert r1.assessment_hash != r2.assessment_hash

    def test_to_dict_contains_expected_keys(self):
        r = self._result()
        d = r.to_dict()
        assert set(d.keys()) == {
            "endpoint",
            "baseline_p95_ms",
            "post_fix_p95_ms",
            "delta_pct",
            "threshold_pct",
            "passed",
            "reason",
            "baseline_sample_n",
            "post_fix_sample_n",
            "assessment_hash",
        }

    def test_to_dict_passed_is_bool(self):
        r = self._result(passed=False)
        assert r.to_dict()["passed"] is False

    def test_to_dict_delta_rounded(self):
        r = self._result(delta_pct=5.12345)
        assert r.to_dict()["delta_pct"] == 5.12


# ─────────────────────────────────────────────────────────────────────────────
# ProofBundle integration — perf_gate_result field
# ─────────────────────────────────────────────────────────────────────────────


class TestProofBundleIntegration:
    def _bundle(self) -> ProofBundle:
        return ProofBundle(
            incident_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
        )

    def test_proof_bundle_accepts_perf_gate_result(self):
        bundle = self._bundle()
        g = _fresh()
        g.record_pre_fix(EP, 100.0)
        g.record_post_fix(EP, 108.0)
        result = g.evaluate(EP)
        bundle.perf_gate_result = result
        assert bundle.perf_gate_result is result
        assert bundle.perf_gate_result.passed is True

    def test_proof_bundle_perf_gate_defaults_to_none(self):
        bundle = self._bundle()
        assert bundle.perf_gate_result is None


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────


class TestModuleSingleton:
    def test_gate_is_performance_gate_instance(self):
        assert isinstance(gate, PerformanceGate)

    def test_default_regression_threshold(self):
        assert gate.regression_threshold == DEFAULT_REGRESSION_THRESHOLD  # 1.15
