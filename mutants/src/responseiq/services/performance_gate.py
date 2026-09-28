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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁPerformanceGateResultǁ__post_init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateResultǁ_compute_hash__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateResultǁto_dict__mutmut: MutantDict = {}  # type: ignore


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

    @_mutmut_mutated(mutants_xǁPerformanceGateResultǁ__post_init____mutmut)
    def __post_init__(self) -> None:
        if not self.assessment_hash:
            self.assessment_hash = self._compute_hash()

    def xǁPerformanceGateResultǁ__post_init____mutmut_orig(self) -> None:
        if not self.assessment_hash:
            self.assessment_hash = self._compute_hash()

    def xǁPerformanceGateResultǁ__post_init____mutmut_1(self) -> None:
        if self.assessment_hash:
            self.assessment_hash = self._compute_hash()

    def xǁPerformanceGateResultǁ__post_init____mutmut_2(self) -> None:
        if not self.assessment_hash:
            self.assessment_hash = None

    @_mutmut_mutated(mutants_xǁPerformanceGateResultǁ_compute_hash__mutmut)
    def _compute_hash(self) -> str:
        import hashlib

        payload = f"{self.endpoint}|{self.baseline_p95_ms:.4f}|{self.post_fix_p95_ms:.4f}|{self.delta_pct:.4f}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def xǁPerformanceGateResultǁ_compute_hash__mutmut_orig(self) -> str:
        import hashlib

        payload = f"{self.endpoint}|{self.baseline_p95_ms:.4f}|{self.post_fix_p95_ms:.4f}|{self.delta_pct:.4f}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def xǁPerformanceGateResultǁ_compute_hash__mutmut_1(self) -> str:
        import hashlib

        payload = None
        return hashlib.sha256(payload.encode()).hexdigest()

    def xǁPerformanceGateResultǁ_compute_hash__mutmut_2(self) -> str:
        import hashlib

        payload = f"{self.endpoint}|{self.baseline_p95_ms:.4f}|{self.post_fix_p95_ms:.4f}|{self.delta_pct:.4f}"
        return hashlib.sha256(None).hexdigest()

    @_mutmut_mutated(mutants_xǁPerformanceGateResultǁto_dict__mutmut)
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

    def xǁPerformanceGateResultǁto_dict__mutmut_orig(self) -> dict:
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

    def xǁPerformanceGateResultǁto_dict__mutmut_1(self) -> dict:
        return {
            "XXendpointXX": self.endpoint,
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

    def xǁPerformanceGateResultǁto_dict__mutmut_2(self) -> dict:
        return {
            "ENDPOINT": self.endpoint,
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

    def xǁPerformanceGateResultǁto_dict__mutmut_3(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "XXbaseline_p95_msXX": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_4(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "BASELINE_P95_MS": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_5(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(None, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_6(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, None),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_7(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_8(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, ),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_9(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 4),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_10(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "XXpost_fix_p95_msXX": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_11(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "POST_FIX_P95_MS": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_12(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(None, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_13(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, None),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_14(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_15(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, ),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_16(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 4),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_17(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "XXdelta_pctXX": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_18(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "DELTA_PCT": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_19(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(None, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_20(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, None),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_21(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_22(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, ),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_23(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 3),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_24(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "XXthreshold_pctXX": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_25(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "THRESHOLD_PCT": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_26(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "XXpassedXX": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_27(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "PASSED": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_28(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "XXreasonXX": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_29(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "REASON": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_30(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "XXbaseline_sample_nXX": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_31(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "BASELINE_SAMPLE_N": self.baseline_sample_n,
            "post_fix_sample_n": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_32(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "XXpost_fix_sample_nXX": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_33(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "baseline_p95_ms": round(self.baseline_p95_ms, 3),
            "post_fix_p95_ms": round(self.post_fix_p95_ms, 3),
            "delta_pct": round(self.delta_pct, 2),
            "threshold_pct": self.threshold_pct,
            "passed": self.passed,
            "reason": self.reason,
            "baseline_sample_n": self.baseline_sample_n,
            "POST_FIX_SAMPLE_N": self.post_fix_sample_n,
            "assessment_hash": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_34(self) -> dict:
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
            "XXassessment_hashXX": self.assessment_hash,
        }

    def xǁPerformanceGateResultǁto_dict__mutmut_35(self) -> dict:
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
            "ASSESSMENT_HASH": self.assessment_hash,
        }

mutants_xǁPerformanceGateResultǁ__post_init____mutmut['_mutmut_orig'] = PerformanceGateResult.xǁPerformanceGateResultǁ__post_init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁ__post_init____mutmut['xǁPerformanceGateResultǁ__post_init____mutmut_1'] = PerformanceGateResult.xǁPerformanceGateResultǁ__post_init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁ__post_init____mutmut['xǁPerformanceGateResultǁ__post_init____mutmut_2'] = PerformanceGateResult.xǁPerformanceGateResultǁ__post_init____mutmut_2 # type: ignore # mutmut generated

mutants_xǁPerformanceGateResultǁ_compute_hash__mutmut['_mutmut_orig'] = PerformanceGateResult.xǁPerformanceGateResultǁ_compute_hash__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁ_compute_hash__mutmut['xǁPerformanceGateResultǁ_compute_hash__mutmut_1'] = PerformanceGateResult.xǁPerformanceGateResultǁ_compute_hash__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁ_compute_hash__mutmut['xǁPerformanceGateResultǁ_compute_hash__mutmut_2'] = PerformanceGateResult.xǁPerformanceGateResultǁ_compute_hash__mutmut_2 # type: ignore # mutmut generated

mutants_xǁPerformanceGateResultǁto_dict__mutmut['_mutmut_orig'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_1'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_2'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_3'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_4'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_5'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_6'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_7'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_8'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_9'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_10'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_11'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_12'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_12 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_13'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_13 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_14'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_14 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_15'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_15 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_16'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_16 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_17'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_17 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_18'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_18 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_19'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_19 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_20'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_20 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_21'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_21 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_22'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_22 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_23'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_23 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_24'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_24 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_25'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_25 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_26'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_26 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_27'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_27 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_28'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_28 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_29'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_29 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_30'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_30 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_31'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_31 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_32'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_32 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_33'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_33 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_34'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_34 # type: ignore # mutmut generated
mutants_xǁPerformanceGateResultǁto_dict__mutmut['xǁPerformanceGateResultǁto_dict__mutmut_35'] = PerformanceGateResult.xǁPerformanceGateResultǁto_dict__mutmut_35 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut: MutantDict = {}  # type: ignore


# ── insufficient data sentinel ────────────────────────────────────────────────


@_mutmut_mutated(mutants_x__insufficient_data_result__mutmut)
def _insufficient_data_result(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_orig(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_1(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=None,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_2(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=None,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_3(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=None,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_4(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=None,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_5(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=None,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_6(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=None,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_7(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=None,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_8(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=None,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_9(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=None,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_10(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_11(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_12(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_13(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_14(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_15(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_16(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_17(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_18(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_19(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=1.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_20(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=1.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_21(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=1.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_22(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=True,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_23(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=1,
        post_fix_sample_n=0,
    )


# ── insufficient data sentinel ────────────────────────────────────────────────


def x__insufficient_data_result__mutmut_24(endpoint: str, reason: str, threshold_pct: float) -> PerformanceGateResult:
    """Return a failed result when there is not enough data to evaluate safely."""
    return PerformanceGateResult(
        endpoint=endpoint,
        baseline_p95_ms=0.0,
        post_fix_p95_ms=0.0,
        delta_pct=0.0,
        threshold_pct=threshold_pct,
        passed=False,
        reason=reason,
        baseline_sample_n=0,
        post_fix_sample_n=1,
    )

mutants_x__insufficient_data_result__mutmut['_mutmut_orig'] = x__insufficient_data_result__mutmut_orig # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_1'] = x__insufficient_data_result__mutmut_1 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_2'] = x__insufficient_data_result__mutmut_2 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_3'] = x__insufficient_data_result__mutmut_3 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_4'] = x__insufficient_data_result__mutmut_4 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_5'] = x__insufficient_data_result__mutmut_5 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_6'] = x__insufficient_data_result__mutmut_6 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_7'] = x__insufficient_data_result__mutmut_7 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_8'] = x__insufficient_data_result__mutmut_8 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_9'] = x__insufficient_data_result__mutmut_9 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_10'] = x__insufficient_data_result__mutmut_10 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_11'] = x__insufficient_data_result__mutmut_11 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_12'] = x__insufficient_data_result__mutmut_12 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_13'] = x__insufficient_data_result__mutmut_13 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_14'] = x__insufficient_data_result__mutmut_14 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_15'] = x__insufficient_data_result__mutmut_15 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_16'] = x__insufficient_data_result__mutmut_16 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_17'] = x__insufficient_data_result__mutmut_17 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_18'] = x__insufficient_data_result__mutmut_18 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_19'] = x__insufficient_data_result__mutmut_19 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_20'] = x__insufficient_data_result__mutmut_20 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_21'] = x__insufficient_data_result__mutmut_21 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_22'] = x__insufficient_data_result__mutmut_22 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_23'] = x__insufficient_data_result__mutmut_23 # type: ignore # mutmut generated
mutants_x__insufficient_data_result__mutmut['x__insufficient_data_result__mutmut_24'] = x__insufficient_data_result__mutmut_24 # type: ignore # mutmut generated
mutants_x__p95__mutmut: MutantDict = {}  # type: ignore


# ── p95 helper ────────────────────────────────────────────────────────────────


@_mutmut_mutated(mutants_x__p95__mutmut)
def _p95(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(0, int(len(sorted_s) * 0.95) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_orig(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(0, int(len(sorted_s) * 0.95) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_1(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(0, int(len(sorted_s) * 0.95) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_2(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 1.0
    sorted_s = sorted(samples)
    idx = max(0, int(len(sorted_s) * 0.95) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_3(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = None
    idx = max(0, int(len(sorted_s) * 0.95) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_4(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(None)
    idx = max(0, int(len(sorted_s) * 0.95) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_5(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = None
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_6(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(None, int(len(sorted_s) * 0.95) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_7(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(0, None)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_8(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(int(len(sorted_s) * 0.95) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_9(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(0, )
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_10(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(1, int(len(sorted_s) * 0.95) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_11(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(0, int(len(sorted_s) * 0.95) + 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_12(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(0, int(None) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_13(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(0, int(len(sorted_s) / 0.95) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_14(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(0, int(len(sorted_s) * 1.95) - 1)
    return sorted_s[idx]


# ── p95 helper ────────────────────────────────────────────────────────────────


def x__p95__mutmut_15(samples: List[float]) -> float:
    """Compute p95 of *samples* using nearest-rank method."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = max(0, int(len(sorted_s) * 0.95) - 2)
    return sorted_s[idx]

mutants_x__p95__mutmut['_mutmut_orig'] = x__p95__mutmut_orig # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_1'] = x__p95__mutmut_1 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_2'] = x__p95__mutmut_2 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_3'] = x__p95__mutmut_3 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_4'] = x__p95__mutmut_4 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_5'] = x__p95__mutmut_5 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_6'] = x__p95__mutmut_6 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_7'] = x__p95__mutmut_7 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_8'] = x__p95__mutmut_8 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_9'] = x__p95__mutmut_9 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_10'] = x__p95__mutmut_10 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_11'] = x__p95__mutmut_11 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_12'] = x__p95__mutmut_12 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_13'] = x__p95__mutmut_13 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_14'] = x__p95__mutmut_14 # type: ignore # mutmut generated
mutants_x__p95__mutmut['x__p95__mutmut_15'] = x__p95__mutmut_15 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateǁrecord__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateǁevaluate__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateǁbaseline_p95__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateǁreset__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateǁ_compare__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateǁ_build_result__mutmut: MutantDict = {}  # type: ignore
mutants_xǁPerformanceGateǁ_emit_otel_event__mutmut: MutantDict = {}  # type: ignore


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

    @_mutmut_mutated(mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut)
    def record_pre_fix(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="pre_fix")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_orig(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="pre_fix")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_1(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(None)
        self._emit_otel_event(endpoint, duration_ms, phase="pre_fix")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_2(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(None, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="pre_fix")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_3(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, None).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="pre_fix")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_4(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault([]).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="pre_fix")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_5(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, ).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="pre_fix")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_6(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(None, duration_ms, phase="pre_fix")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_7(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, None, phase="pre_fix")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_8(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase=None)

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_9(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(duration_ms, phase="pre_fix")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_10(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, phase="pre_fix")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_11(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, )

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_12(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="XXpre_fixXX")

    # ── recording ─────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁrecord_pre_fix__mutmut_13(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured BEFORE the fix was applied."""
        self._pre_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="PRE_FIX")

    @_mutmut_mutated(mutants_xǁPerformanceGateǁrecord_post_fix__mutmut)
    def record_post_fix(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="post_fix")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_orig(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="post_fix")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_1(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(None)
        self._emit_otel_event(endpoint, duration_ms, phase="post_fix")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_2(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(None, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="post_fix")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_3(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, None).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="post_fix")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_4(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault([]).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="post_fix")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_5(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, ).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="post_fix")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_6(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(None, duration_ms, phase="post_fix")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_7(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, None, phase="post_fix")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_8(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase=None)

    def xǁPerformanceGateǁrecord_post_fix__mutmut_9(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(duration_ms, phase="post_fix")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_10(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, phase="post_fix")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_11(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, )

    def xǁPerformanceGateǁrecord_post_fix__mutmut_12(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="XXpost_fixXX")

    def xǁPerformanceGateǁrecord_post_fix__mutmut_13(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample measured AFTER the fix was applied."""
        self._post_fix.setdefault(endpoint, []).append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="POST_FIX")

    @_mutmut_mutated(mutants_xǁPerformanceGateǁrecord__mutmut)
    def record(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="rolling")

    def xǁPerformanceGateǁrecord__mutmut_orig(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="rolling")

    def xǁPerformanceGateǁrecord__mutmut_1(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="rolling")

    def xǁPerformanceGateǁrecord__mutmut_2(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = None
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="rolling")

    def xǁPerformanceGateǁrecord__mutmut_3(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=None)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="rolling")

    def xǁPerformanceGateǁrecord__mutmut_4(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(None)
        self._emit_otel_event(endpoint, duration_ms, phase="rolling")

    def xǁPerformanceGateǁrecord__mutmut_5(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(None, duration_ms, phase="rolling")

    def xǁPerformanceGateǁrecord__mutmut_6(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, None, phase="rolling")

    def xǁPerformanceGateǁrecord__mutmut_7(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase=None)

    def xǁPerformanceGateǁrecord__mutmut_8(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(duration_ms, phase="rolling")

    def xǁPerformanceGateǁrecord__mutmut_9(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, phase="rolling")

    def xǁPerformanceGateǁrecord__mutmut_10(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, )

    def xǁPerformanceGateǁrecord__mutmut_11(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="XXrollingXX")

    def xǁPerformanceGateǁrecord__mutmut_12(self, endpoint: str, duration_ms: float) -> None:
        """Record a latency sample in the rolling production window."""
        if endpoint not in self._rolling:
            self._rolling[endpoint] = deque(maxlen=self.window_size)
        self._rolling[endpoint].append(duration_ms)
        self._emit_otel_event(endpoint, duration_ms, phase="ROLLING")

    @_mutmut_mutated(mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut)
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_orig(self, endpoint: str) -> Optional[float]:
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_1(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = None
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_2(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(None)
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_3(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(None, []))
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_4(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, None))
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_5(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get([]))
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_6(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, ))
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_7(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if window:
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_8(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if not window:
            logger.warning(None, endpoint)
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_9(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if not window:
            logger.warning("PerformanceGate: no rolling samples for '%s'; baseline not set", None)
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_10(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if not window:
            logger.warning(endpoint)
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_11(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if not window:
            logger.warning("PerformanceGate: no rolling samples for '%s'; baseline not set", )
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_12(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if not window:
            logger.warning("XXPerformanceGate: no rolling samples for '%s'; baseline not setXX", endpoint)
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_13(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if not window:
            logger.warning("performancegate: no rolling samples for '%s'; baseline not set", endpoint)
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_14(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if not window:
            logger.warning("PERFORMANCEGATE: NO ROLLING SAMPLES FOR '%S'; BASELINE NOT SET", endpoint)
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

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_15(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if not window:
            logger.warning("PerformanceGate: no rolling samples for '%s'; baseline not set", endpoint)
            return None
        baseline = None
        self._baseline_snapshot[endpoint] = baseline
        logger.info(
            "PerformanceGate: baseline snapshotted",
            endpoint=endpoint,
            p95_ms=round(baseline, 3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_16(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if not window:
            logger.warning("PerformanceGate: no rolling samples for '%s'; baseline not set", endpoint)
            return None
        baseline = _p95(None)
        self._baseline_snapshot[endpoint] = baseline
        logger.info(
            "PerformanceGate: baseline snapshotted",
            endpoint=endpoint,
            p95_ms=round(baseline, 3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_17(self, endpoint: str) -> Optional[float]:
        """Freeze the current rolling p95 as the baseline for *endpoint*.

        Returns the frozen p95 value, or None if there are no rolling samples.
        """
        window = list(self._rolling.get(endpoint, []))
        if not window:
            logger.warning("PerformanceGate: no rolling samples for '%s'; baseline not set", endpoint)
            return None
        baseline = _p95(window)
        self._baseline_snapshot[endpoint] = None
        logger.info(
            "PerformanceGate: baseline snapshotted",
            endpoint=endpoint,
            p95_ms=round(baseline, 3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_18(self, endpoint: str) -> Optional[float]:
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
            None,
            endpoint=endpoint,
            p95_ms=round(baseline, 3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_19(self, endpoint: str) -> Optional[float]:
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
            endpoint=None,
            p95_ms=round(baseline, 3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_20(self, endpoint: str) -> Optional[float]:
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
            p95_ms=None,
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_21(self, endpoint: str) -> Optional[float]:
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
            n=None,
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_22(self, endpoint: str) -> Optional[float]:
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
            endpoint=endpoint,
            p95_ms=round(baseline, 3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_23(self, endpoint: str) -> Optional[float]:
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
            p95_ms=round(baseline, 3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_24(self, endpoint: str) -> Optional[float]:
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
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_25(self, endpoint: str) -> Optional[float]:
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
            )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_26(self, endpoint: str) -> Optional[float]:
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
            "XXPerformanceGate: baseline snapshottedXX",
            endpoint=endpoint,
            p95_ms=round(baseline, 3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_27(self, endpoint: str) -> Optional[float]:
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
            "performancegate: baseline snapshotted",
            endpoint=endpoint,
            p95_ms=round(baseline, 3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_28(self, endpoint: str) -> Optional[float]:
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
            "PERFORMANCEGATE: BASELINE SNAPSHOTTED",
            endpoint=endpoint,
            p95_ms=round(baseline, 3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_29(self, endpoint: str) -> Optional[float]:
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
            p95_ms=round(None, 3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_30(self, endpoint: str) -> Optional[float]:
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
            p95_ms=round(baseline, None),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_31(self, endpoint: str) -> Optional[float]:
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
            p95_ms=round(3),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_32(self, endpoint: str) -> Optional[float]:
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
            p95_ms=round(baseline, ),
            n=len(window),
        )
        return baseline

    def xǁPerformanceGateǁsnapshot_baseline__mutmut_33(self, endpoint: str) -> Optional[float]:
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
            p95_ms=round(baseline, 4),
            n=len(window),
        )
        return baseline

    # ── evaluation ────────────────────────────────────────────────────────────

    @_mutmut_mutated(mutants_xǁPerformanceGateǁevaluate__mutmut)
    def evaluate(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_orig(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_1(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = None
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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_2(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if (threshold is not None) and False else self.regression_threshold
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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_3(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if (threshold is not None) or True else self.regression_threshold
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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_4(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is None else self.regression_threshold
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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_5(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is not None else self.regression_threshold
        threshold_pct = None

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_6(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is not None else self.regression_threshold
        threshold_pct = (thr - 1.0) / 100.0

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_7(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is not None else self.regression_threshold
        threshold_pct = (thr + 1.0) * 100.0

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_8(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is not None else self.regression_threshold
        threshold_pct = (thr - 2.0) * 100.0

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_9(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is not None else self.regression_threshold
        threshold_pct = (thr - 1.0) * 101.0

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_10(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is not None else self.regression_threshold
        threshold_pct = (thr - 1.0) * 100.0

        # Strategy 1: explicit pre/post samples
        pre_samples = None
        post_samples = self._post_fix.get(endpoint, [])

        if pre_samples and post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_11(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is not None else self.regression_threshold
        threshold_pct = (thr - 1.0) * 100.0

        # Strategy 1: explicit pre/post samples
        pre_samples = self._pre_fix.get(None, [])
        post_samples = self._post_fix.get(endpoint, [])

        if pre_samples and post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_12(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is not None else self.regression_threshold
        threshold_pct = (thr - 1.0) * 100.0

        # Strategy 1: explicit pre/post samples
        pre_samples = self._pre_fix.get(endpoint, None)
        post_samples = self._post_fix.get(endpoint, [])

        if pre_samples and post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_13(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is not None else self.regression_threshold
        threshold_pct = (thr - 1.0) * 100.0

        # Strategy 1: explicit pre/post samples
        pre_samples = self._pre_fix.get([])
        post_samples = self._post_fix.get(endpoint, [])

        if pre_samples and post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_14(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

        Args:
            endpoint:  The operation name to evaluate.
            threshold: Override the instance regression_threshold (1.15 = 15%).

        Returns:
            PerformanceGateResult with passed=True/False and full diagnostics.
        """
        thr = threshold if threshold is not None else self.regression_threshold
        threshold_pct = (thr - 1.0) * 100.0

        # Strategy 1: explicit pre/post samples
        pre_samples = self._pre_fix.get(endpoint, )
        post_samples = self._post_fix.get(endpoint, [])

        if pre_samples and post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_15(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        post_samples = None

        if pre_samples and post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_16(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        post_samples = self._post_fix.get(None, [])

        if pre_samples and post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_17(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        post_samples = self._post_fix.get(endpoint, None)

        if pre_samples and post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_18(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        post_samples = self._post_fix.get([])

        if pre_samples and post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_19(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        post_samples = self._post_fix.get(endpoint, )

        if pre_samples and post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_20(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        if pre_samples or post_samples:
            return self._compare(endpoint, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_21(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare(None, pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_22(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare(endpoint, None, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_23(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare(endpoint, pre_samples, None, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_24(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare(endpoint, pre_samples, post_samples, None, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_25(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare(endpoint, pre_samples, post_samples, thr, None)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_26(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare(pre_samples, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_27(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare(endpoint, post_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_28(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare(endpoint, pre_samples, thr, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_29(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare(endpoint, pre_samples, post_samples, threshold_pct)

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_30(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare(endpoint, pre_samples, post_samples, thr, )

        # Strategy 2: snapshot baseline + rolling window
        baseline_p95 = self._baseline_snapshot.get(endpoint)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_31(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        baseline_p95 = None
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_32(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        baseline_p95 = self._baseline_snapshot.get(None)
        rolling = list(self._rolling.get(endpoint, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_33(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        rolling = None

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_34(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        rolling = list(None)

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_35(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        rolling = list(self._rolling.get(None, []))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_36(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        rolling = list(self._rolling.get(endpoint, None))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_37(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        rolling = list(self._rolling.get([]))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_38(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
        rolling = list(self._rolling.get(endpoint, ))

        if baseline_p95 is not None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_39(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        if baseline_p95 is not None or rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_40(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        if baseline_p95 is None and rolling:
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_41(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare_snapshot(None, baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_42(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare_snapshot(endpoint, None, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_43(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare_snapshot(endpoint, baseline_p95, None, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_44(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare_snapshot(endpoint, baseline_p95, rolling, None, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_45(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, None)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_46(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare_snapshot(baseline_p95, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_47(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare_snapshot(endpoint, rolling, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_48(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare_snapshot(endpoint, baseline_p95, thr, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_49(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare_snapshot(endpoint, baseline_p95, rolling, threshold_pct)

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_50(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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
            return self._compare_snapshot(endpoint, baseline_p95, rolling, thr, )

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_51(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(None, "insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_52(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, None, threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_53(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", None)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_54(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result("insufficient_data: no baseline available", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_55(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_56(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "insufficient_data: no baseline available", )

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_57(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "XXinsufficient_data: no baseline availableXX", threshold_pct)

    # ── evaluation ────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁevaluate__mutmut_58(
        self,
        endpoint: str,
        threshold: Optional[float] = None,
    ) -> PerformanceGateResult:
        """Evaluate whether post-fix latency regresses beyond *threshold*.

        Evaluation strategy (in order):
          1. If pre_fix + post_fix samples exist → use them directly.
          2. If a baseline snapshot + rolling samples exist → use them.
          3. Not enough data → fail closed with reason "insufficient_data".

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

        # Strategy 3: insufficient data — gate fails closed.
        return _insufficient_data_result(endpoint, "INSUFFICIENT_DATA: NO BASELINE AVAILABLE", threshold_pct)

    @_mutmut_mutated(mutants_xǁPerformanceGateǁbaseline_p95__mutmut)
    def baseline_p95(self, endpoint: str) -> Optional[float]:
        """Return the current baseline p95 for *endpoint*, or None."""
        return self._baseline_snapshot.get(endpoint) or (
            _p95(self._pre_fix[endpoint]) if self._pre_fix.get(endpoint) else None
        )

    def xǁPerformanceGateǁbaseline_p95__mutmut_orig(self, endpoint: str) -> Optional[float]:
        """Return the current baseline p95 for *endpoint*, or None."""
        return self._baseline_snapshot.get(endpoint) or (
            _p95(self._pre_fix[endpoint]) if self._pre_fix.get(endpoint) else None
        )

    def xǁPerformanceGateǁbaseline_p95__mutmut_1(self, endpoint: str) -> Optional[float]:
        """Return the current baseline p95 for *endpoint*, or None."""
        return self._baseline_snapshot.get(endpoint) and (
            _p95(self._pre_fix[endpoint]) if self._pre_fix.get(endpoint) else None
        )

    def xǁPerformanceGateǁbaseline_p95__mutmut_2(self, endpoint: str) -> Optional[float]:
        """Return the current baseline p95 for *endpoint*, or None."""
        return self._baseline_snapshot.get(None) or (
            _p95(self._pre_fix[endpoint]) if self._pre_fix.get(endpoint) else None
        )

    def xǁPerformanceGateǁbaseline_p95__mutmut_3(self, endpoint: str) -> Optional[float]:
        """Return the current baseline p95 for *endpoint*, or None."""
        return self._baseline_snapshot.get(endpoint) or (
            _p95(self._pre_fix[endpoint]) if (self._pre_fix.get(endpoint)) and False else None
        )

    def xǁPerformanceGateǁbaseline_p95__mutmut_4(self, endpoint: str) -> Optional[float]:
        """Return the current baseline p95 for *endpoint*, or None."""
        return self._baseline_snapshot.get(endpoint) or (
            _p95(self._pre_fix[endpoint]) if (self._pre_fix.get(endpoint)) or True else None
        )

    def xǁPerformanceGateǁbaseline_p95__mutmut_5(self, endpoint: str) -> Optional[float]:
        """Return the current baseline p95 for *endpoint*, or None."""
        return self._baseline_snapshot.get(endpoint) or (
            _p95(None) if self._pre_fix.get(endpoint) else None
        )

    def xǁPerformanceGateǁbaseline_p95__mutmut_6(self, endpoint: str) -> Optional[float]:
        """Return the current baseline p95 for *endpoint*, or None."""
        return self._baseline_snapshot.get(endpoint) or (
            _p95(self._pre_fix[endpoint]) if self._pre_fix.get(None) else None
        )

    # ── reset ─────────────────────────────────────────────────────────────────

    @_mutmut_mutated(mutants_xǁPerformanceGateǁreset__mutmut)
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

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_orig(self, endpoint: Optional[str] = None) -> None:
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

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_1(self, endpoint: Optional[str] = None) -> None:
        """Reset samples for *endpoint* (or ALL endpoints if None).

        Useful between tests and between remediation runs to avoid cross-run
        contamination.
        """
        if endpoint is not None:
            self._pre_fix.clear()
            self._post_fix.clear()
            self._rolling.clear()
            self._baseline_snapshot.clear()
        else:
            self._pre_fix.pop(endpoint, None)
            self._post_fix.pop(endpoint, None)
            self._rolling.pop(endpoint, None)
            self._baseline_snapshot.pop(endpoint, None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_2(self, endpoint: Optional[str] = None) -> None:
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
            self._pre_fix.pop(None, None)
            self._post_fix.pop(endpoint, None)
            self._rolling.pop(endpoint, None)
            self._baseline_snapshot.pop(endpoint, None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_3(self, endpoint: Optional[str] = None) -> None:
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
            self._pre_fix.pop(None)
            self._post_fix.pop(endpoint, None)
            self._rolling.pop(endpoint, None)
            self._baseline_snapshot.pop(endpoint, None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_4(self, endpoint: Optional[str] = None) -> None:
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
            self._pre_fix.pop(endpoint, )
            self._post_fix.pop(endpoint, None)
            self._rolling.pop(endpoint, None)
            self._baseline_snapshot.pop(endpoint, None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_5(self, endpoint: Optional[str] = None) -> None:
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
            self._post_fix.pop(None, None)
            self._rolling.pop(endpoint, None)
            self._baseline_snapshot.pop(endpoint, None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_6(self, endpoint: Optional[str] = None) -> None:
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
            self._post_fix.pop(None)
            self._rolling.pop(endpoint, None)
            self._baseline_snapshot.pop(endpoint, None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_7(self, endpoint: Optional[str] = None) -> None:
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
            self._post_fix.pop(endpoint, )
            self._rolling.pop(endpoint, None)
            self._baseline_snapshot.pop(endpoint, None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_8(self, endpoint: Optional[str] = None) -> None:
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
            self._rolling.pop(None, None)
            self._baseline_snapshot.pop(endpoint, None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_9(self, endpoint: Optional[str] = None) -> None:
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
            self._rolling.pop(None)
            self._baseline_snapshot.pop(endpoint, None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_10(self, endpoint: Optional[str] = None) -> None:
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
            self._rolling.pop(endpoint, )
            self._baseline_snapshot.pop(endpoint, None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_11(self, endpoint: Optional[str] = None) -> None:
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
            self._baseline_snapshot.pop(None, None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_12(self, endpoint: Optional[str] = None) -> None:
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
            self._baseline_snapshot.pop(None)

    # ── reset ─────────────────────────────────────────────────────────────────

    def xǁPerformanceGateǁreset__mutmut_13(self, endpoint: Optional[str] = None) -> None:
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
            self._baseline_snapshot.pop(endpoint, )

    # ── internal helpers ──────────────────────────────────────────────────────

    @_mutmut_mutated(mutants_xǁPerformanceGateǁ_compare__mutmut)
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

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_orig(
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

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_1(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = None
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, post, thr, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_2(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(None)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, post, thr, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_3(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = None
        return self._build_result(endpoint, baseline, post, thr, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_4(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(None)
        return self._build_result(endpoint, baseline, post, thr, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_5(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(None, baseline, post, thr, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_6(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, None, post, thr, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_7(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, None, thr, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_8(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, post, None, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_9(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, post, thr, None, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_10(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, post, thr, threshold_pct, None, len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_11(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, post, thr, threshold_pct, len(pre_samples), None)

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_12(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(baseline, post, thr, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_13(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, post, thr, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_14(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, thr, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_15(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, post, threshold_pct, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_16(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, post, thr, len(pre_samples), len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_17(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, post, thr, threshold_pct, len(post_samples))

    # ── internal helpers ──────────────────────────────────────────────────────

    def xǁPerformanceGateǁ_compare__mutmut_18(
        self,
        endpoint: str,
        pre_samples: List[float],
        post_samples: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        baseline = _p95(pre_samples)
        post = _p95(post_samples)
        return self._build_result(endpoint, baseline, post, thr, threshold_pct, len(pre_samples), )

    @_mutmut_mutated(mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut)
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

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_orig(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, post, thr, threshold_pct, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_1(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = None
        return self._build_result(endpoint, baseline_p95, post, thr, threshold_pct, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_2(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(None)
        return self._build_result(endpoint, baseline_p95, post, thr, threshold_pct, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_3(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(None, baseline_p95, post, thr, threshold_pct, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_4(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, None, post, thr, threshold_pct, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_5(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, None, thr, threshold_pct, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_6(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, post, None, threshold_pct, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_7(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, post, thr, None, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_8(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, post, thr, threshold_pct, None, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_9(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, post, thr, threshold_pct, 0, None)

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_10(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(baseline_p95, post, thr, threshold_pct, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_11(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, post, thr, threshold_pct, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_12(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, thr, threshold_pct, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_13(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, post, threshold_pct, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_14(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, post, thr, 0, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_15(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, post, thr, threshold_pct, len(rolling))

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_16(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, post, thr, threshold_pct, 0, )

    def xǁPerformanceGateǁ_compare_snapshot__mutmut_17(
        self,
        endpoint: str,
        baseline_p95: float,
        rolling: List[float],
        thr: float,
        threshold_pct: float,
    ) -> PerformanceGateResult:
        post = _p95(rolling)
        return self._build_result(endpoint, baseline_p95, post, thr, threshold_pct, 1, len(rolling))

    @_mutmut_mutated(mutants_xǁPerformanceGateǁ_build_result__mutmut)
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

    def xǁPerformanceGateǁ_build_result__mutmut_orig(
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

    def xǁPerformanceGateǁ_build_result__mutmut_1(
        self,
        endpoint: str,
        baseline: float,
        post: float,
        thr: float,
        threshold_pct: float,
        n_baseline: int,
        n_post: int,
    ) -> PerformanceGateResult:
        if baseline != 0.0:
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

    def xǁPerformanceGateǁ_build_result__mutmut_2(
        self,
        endpoint: str,
        baseline: float,
        post: float,
        thr: float,
        threshold_pct: float,
        n_baseline: int,
        n_post: int,
    ) -> PerformanceGateResult:
        if baseline == 1.0:
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

    def xǁPerformanceGateǁ_build_result__mutmut_3(
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
            delta_pct = None
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

    def xǁPerformanceGateǁ_build_result__mutmut_4(
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
            delta_pct = 1.0
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

    def xǁPerformanceGateǁ_build_result__mutmut_5(
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
            passed = None
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

    def xǁPerformanceGateǁ_build_result__mutmut_6(
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
            passed = False
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

    def xǁPerformanceGateǁ_build_result__mutmut_7(
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
            reason = None
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

    def xǁPerformanceGateǁ_build_result__mutmut_8(
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
            reason = "XXbaseline_zero: gate passesXX"
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

    def xǁPerformanceGateǁ_build_result__mutmut_9(
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
            reason = "BASELINE_ZERO: GATE PASSES"
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

    def xǁPerformanceGateǁ_build_result__mutmut_10(
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
            delta = None
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

    def xǁPerformanceGateǁ_build_result__mutmut_11(
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
            delta = (post - baseline) * baseline
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

    def xǁPerformanceGateǁ_build_result__mutmut_12(
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
            delta = (post + baseline) / baseline
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

    def xǁPerformanceGateǁ_build_result__mutmut_13(
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
            delta_pct = None
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

    def xǁPerformanceGateǁ_build_result__mutmut_14(
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
            delta_pct = delta / 100.0
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

    def xǁPerformanceGateǁ_build_result__mutmut_15(
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
            delta_pct = delta * 101.0
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

    def xǁPerformanceGateǁ_build_result__mutmut_16(
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
            passed = None
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

    def xǁPerformanceGateǁ_build_result__mutmut_17(
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
            passed = post < baseline * thr
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

    def xǁPerformanceGateǁ_build_result__mutmut_18(
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
            passed = post <= baseline / thr
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

    def xǁPerformanceGateǁ_build_result__mutmut_19(
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
                reason = None
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

    def xǁPerformanceGateǁ_build_result__mutmut_20(
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
                reason = None

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

    def xǁPerformanceGateǁ_build_result__mutmut_21(
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

        result = None

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

    def xǁPerformanceGateǁ_build_result__mutmut_22(
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
            endpoint=None,
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

    def xǁPerformanceGateǁ_build_result__mutmut_23(
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
            baseline_p95_ms=None,
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

    def xǁPerformanceGateǁ_build_result__mutmut_24(
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
            post_fix_p95_ms=None,
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

    def xǁPerformanceGateǁ_build_result__mutmut_25(
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
            delta_pct=None,
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

    def xǁPerformanceGateǁ_build_result__mutmut_26(
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
            threshold_pct=None,
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

    def xǁPerformanceGateǁ_build_result__mutmut_27(
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
            passed=None,
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

    def xǁPerformanceGateǁ_build_result__mutmut_28(
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
            reason=None,
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

    def xǁPerformanceGateǁ_build_result__mutmut_29(
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
            baseline_sample_n=None,
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

    def xǁPerformanceGateǁ_build_result__mutmut_30(
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
            post_fix_sample_n=None,
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

    def xǁPerformanceGateǁ_build_result__mutmut_31(
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

    def xǁPerformanceGateǁ_build_result__mutmut_32(
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

    def xǁPerformanceGateǁ_build_result__mutmut_33(
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

    def xǁPerformanceGateǁ_build_result__mutmut_34(
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

    def xǁPerformanceGateǁ_build_result__mutmut_35(
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

    def xǁPerformanceGateǁ_build_result__mutmut_36(
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

    def xǁPerformanceGateǁ_build_result__mutmut_37(
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

    def xǁPerformanceGateǁ_build_result__mutmut_38(
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

    def xǁPerformanceGateǁ_build_result__mutmut_39(
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

    def xǁPerformanceGateǁ_build_result__mutmut_40(
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
            baseline_p95_ms=round(None, 3),
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

    def xǁPerformanceGateǁ_build_result__mutmut_41(
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
            baseline_p95_ms=round(baseline, None),
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

    def xǁPerformanceGateǁ_build_result__mutmut_42(
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
            baseline_p95_ms=round(3),
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

    def xǁPerformanceGateǁ_build_result__mutmut_43(
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
            baseline_p95_ms=round(baseline, ),
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

    def xǁPerformanceGateǁ_build_result__mutmut_44(
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
            baseline_p95_ms=round(baseline, 4),
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

    def xǁPerformanceGateǁ_build_result__mutmut_45(
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
            post_fix_p95_ms=round(None, 3),
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

    def xǁPerformanceGateǁ_build_result__mutmut_46(
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
            post_fix_p95_ms=round(post, None),
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

    def xǁPerformanceGateǁ_build_result__mutmut_47(
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
            post_fix_p95_ms=round(3),
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

    def xǁPerformanceGateǁ_build_result__mutmut_48(
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
            post_fix_p95_ms=round(post, ),
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

    def xǁPerformanceGateǁ_build_result__mutmut_49(
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
            post_fix_p95_ms=round(post, 4),
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

    def xǁPerformanceGateǁ_build_result__mutmut_50(
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
            delta_pct=round(None, 2),
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

    def xǁPerformanceGateǁ_build_result__mutmut_51(
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
            delta_pct=round(delta_pct, None),
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

    def xǁPerformanceGateǁ_build_result__mutmut_52(
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
            delta_pct=round(2),
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

    def xǁPerformanceGateǁ_build_result__mutmut_53(
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
            delta_pct=round(delta_pct, ),
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

    def xǁPerformanceGateǁ_build_result__mutmut_54(
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
            delta_pct=round(delta_pct, 3),
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

    def xǁPerformanceGateǁ_build_result__mutmut_55(
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

        level = None
        getattr(logger, level)(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_56(
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

        level = "info" if (passed) and False else "warning"
        getattr(logger, level)(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_57(
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

        level = "info" if (passed) or True else "warning"
        getattr(logger, level)(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_58(
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

        level = "XXinfoXX" if passed else "warning"
        getattr(logger, level)(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_59(
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

        level = "INFO" if passed else "warning"
        getattr(logger, level)(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_60(
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

        level = "info" if passed else "XXwarningXX"
        getattr(logger, level)(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_61(
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

        level = "info" if passed else "WARNING"
        getattr(logger, level)(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_62(
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
            None,
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_63(
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
            endpoint=None,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_64(
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
            passed=None,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_65(
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
            baseline_p95_ms=None,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_66(
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
            post_fix_p95_ms=None,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_67(
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
            delta_pct=None,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_68(
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
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_69(
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
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_70(
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
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_71(
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
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_72(
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
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_73(
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
            )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_74(
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
        getattr(None, level)(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_75(
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
        getattr(logger, None)(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_76(
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
        getattr(level)(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_77(
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
        getattr(logger, )(
            "PerformanceGate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_78(
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
            "XXPerformanceGate evaluationXX",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_79(
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
            "performancegate evaluation",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    def xǁPerformanceGateǁ_build_result__mutmut_80(
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
            "PERFORMANCEGATE EVALUATION",
            endpoint=endpoint,
            passed=passed,
            baseline_p95_ms=result.baseline_p95_ms,
            post_fix_p95_ms=result.post_fix_p95_ms,
            delta_pct=result.delta_pct,
        )
        return result

    @staticmethod
    @_mutmut_mutated(mutants_xǁPerformanceGateǁ_emit_otel_event__mutmut)
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

    @staticmethod
    def xǁPerformanceGateǁ_emit_otel_event__mutmut_orig(endpoint: str, duration_ms: float, phase: str) -> None:
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

    @staticmethod
    def xǁPerformanceGateǁ_emit_otel_event__mutmut_1(endpoint: str, duration_ms: float, phase: str) -> None:
        """Emit a span event to the active OTel span if one exists.

        No-op when no span is active (tests, batch CLI).
        """
        try:
            from opentelemetry import trace

            span = None
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

    @staticmethod
    def xǁPerformanceGateǁ_emit_otel_event__mutmut_2(endpoint: str, duration_ms: float, phase: str) -> None:
        """Emit a span event to the active OTel span if one exists.

        No-op when no span is active (tests, batch CLI).
        """
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span or span.is_recording():
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

mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['_mutmut_orig'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_1'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_2'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_3'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_4'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_5'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_6'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_7'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_8'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_9'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_10'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_11'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_12'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_12 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_pre_fix__mutmut['xǁPerformanceGateǁrecord_pre_fix__mutmut_13'] = PerformanceGate.xǁPerformanceGateǁrecord_pre_fix__mutmut_13 # type: ignore # mutmut generated

mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['_mutmut_orig'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_1'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_2'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_3'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_4'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_5'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_6'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_7'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_8'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_9'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_10'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_11'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_12'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_12 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord_post_fix__mutmut['xǁPerformanceGateǁrecord_post_fix__mutmut_13'] = PerformanceGate.xǁPerformanceGateǁrecord_post_fix__mutmut_13 # type: ignore # mutmut generated

mutants_xǁPerformanceGateǁrecord__mutmut['_mutmut_orig'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_1'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_2'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_3'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_4'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_5'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_6'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_7'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_8'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_9'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_10'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_11'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁrecord__mutmut['xǁPerformanceGateǁrecord__mutmut_12'] = PerformanceGate.xǁPerformanceGateǁrecord__mutmut_12 # type: ignore # mutmut generated

mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['_mutmut_orig'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_1'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_2'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_3'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_4'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_5'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_6'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_7'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_8'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_9'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_10'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_11'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_12'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_12 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_13'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_13 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_14'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_14 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_15'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_15 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_16'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_16 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_17'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_17 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_18'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_18 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_19'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_19 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_20'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_20 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_21'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_21 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_22'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_22 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_23'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_23 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_24'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_24 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_25'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_25 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_26'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_26 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_27'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_27 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_28'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_28 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_29'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_29 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_30'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_30 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_31'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_31 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_32'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_32 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁsnapshot_baseline__mutmut['xǁPerformanceGateǁsnapshot_baseline__mutmut_33'] = PerformanceGate.xǁPerformanceGateǁsnapshot_baseline__mutmut_33 # type: ignore # mutmut generated

mutants_xǁPerformanceGateǁevaluate__mutmut['_mutmut_orig'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_1'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_2'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_3'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_4'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_5'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_6'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_7'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_8'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_9'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_10'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_11'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_12'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_12 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_13'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_13 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_14'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_14 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_15'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_15 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_16'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_16 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_17'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_17 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_18'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_18 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_19'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_19 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_20'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_20 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_21'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_21 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_22'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_22 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_23'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_23 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_24'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_24 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_25'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_25 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_26'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_26 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_27'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_27 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_28'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_28 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_29'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_29 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_30'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_30 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_31'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_31 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_32'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_32 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_33'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_33 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_34'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_34 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_35'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_35 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_36'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_36 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_37'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_37 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_38'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_38 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_39'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_39 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_40'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_40 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_41'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_41 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_42'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_42 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_43'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_43 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_44'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_44 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_45'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_45 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_46'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_46 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_47'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_47 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_48'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_48 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_49'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_49 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_50'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_50 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_51'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_51 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_52'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_52 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_53'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_53 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_54'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_54 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_55'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_55 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_56'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_56 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_57'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_57 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁevaluate__mutmut['xǁPerformanceGateǁevaluate__mutmut_58'] = PerformanceGate.xǁPerformanceGateǁevaluate__mutmut_58 # type: ignore # mutmut generated

mutants_xǁPerformanceGateǁbaseline_p95__mutmut['_mutmut_orig'] = PerformanceGate.xǁPerformanceGateǁbaseline_p95__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁbaseline_p95__mutmut['xǁPerformanceGateǁbaseline_p95__mutmut_1'] = PerformanceGate.xǁPerformanceGateǁbaseline_p95__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁbaseline_p95__mutmut['xǁPerformanceGateǁbaseline_p95__mutmut_2'] = PerformanceGate.xǁPerformanceGateǁbaseline_p95__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁbaseline_p95__mutmut['xǁPerformanceGateǁbaseline_p95__mutmut_3'] = PerformanceGate.xǁPerformanceGateǁbaseline_p95__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁbaseline_p95__mutmut['xǁPerformanceGateǁbaseline_p95__mutmut_4'] = PerformanceGate.xǁPerformanceGateǁbaseline_p95__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁbaseline_p95__mutmut['xǁPerformanceGateǁbaseline_p95__mutmut_5'] = PerformanceGate.xǁPerformanceGateǁbaseline_p95__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁbaseline_p95__mutmut['xǁPerformanceGateǁbaseline_p95__mutmut_6'] = PerformanceGate.xǁPerformanceGateǁbaseline_p95__mutmut_6 # type: ignore # mutmut generated

mutants_xǁPerformanceGateǁreset__mutmut['_mutmut_orig'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_1'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_2'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_3'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_4'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_5'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_6'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_7'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_8'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_9'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_10'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_11'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_12'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_12 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁreset__mutmut['xǁPerformanceGateǁreset__mutmut_13'] = PerformanceGate.xǁPerformanceGateǁreset__mutmut_13 # type: ignore # mutmut generated

mutants_xǁPerformanceGateǁ_compare__mutmut['_mutmut_orig'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_1'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_2'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_3'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_4'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_5'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_6'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_7'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_8'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_9'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_10'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_11'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_12'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_12 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_13'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_13 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_14'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_14 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_15'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_15 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_16'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_16 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_17'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_17 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare__mutmut['xǁPerformanceGateǁ_compare__mutmut_18'] = PerformanceGate.xǁPerformanceGateǁ_compare__mutmut_18 # type: ignore # mutmut generated

mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['_mutmut_orig'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_1'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_2'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_3'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_4'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_5'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_6'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_7'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_8'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_9'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_10'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_11'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_12'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_12 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_13'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_13 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_14'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_14 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_15'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_15 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_16'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_16 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_compare_snapshot__mutmut['xǁPerformanceGateǁ_compare_snapshot__mutmut_17'] = PerformanceGate.xǁPerformanceGateǁ_compare_snapshot__mutmut_17 # type: ignore # mutmut generated

mutants_xǁPerformanceGateǁ_build_result__mutmut['_mutmut_orig'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_1'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_2'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_2 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_3'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_3 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_4'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_4 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_5'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_5 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_6'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_6 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_7'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_7 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_8'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_8 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_9'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_9 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_10'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_10 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_11'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_11 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_12'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_12 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_13'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_13 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_14'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_14 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_15'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_15 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_16'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_16 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_17'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_17 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_18'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_18 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_19'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_19 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_20'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_20 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_21'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_21 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_22'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_22 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_23'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_23 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_24'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_24 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_25'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_25 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_26'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_26 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_27'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_27 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_28'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_28 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_29'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_29 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_30'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_30 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_31'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_31 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_32'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_32 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_33'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_33 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_34'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_34 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_35'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_35 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_36'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_36 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_37'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_37 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_38'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_38 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_39'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_39 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_40'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_40 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_41'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_41 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_42'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_42 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_43'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_43 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_44'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_44 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_45'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_45 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_46'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_46 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_47'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_47 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_48'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_48 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_49'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_49 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_50'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_50 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_51'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_51 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_52'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_52 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_53'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_53 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_54'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_54 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_55'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_55 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_56'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_56 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_57'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_57 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_58'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_58 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_59'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_59 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_60'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_60 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_61'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_61 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_62'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_62 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_63'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_63 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_64'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_64 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_65'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_65 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_66'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_66 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_67'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_67 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_68'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_68 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_69'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_69 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_70'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_70 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_71'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_71 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_72'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_72 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_73'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_73 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_74'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_74 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_75'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_75 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_76'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_76 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_77'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_77 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_78'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_78 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_79'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_79 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_build_result__mutmut['xǁPerformanceGateǁ_build_result__mutmut_80'] = PerformanceGate.xǁPerformanceGateǁ_build_result__mutmut_80 # type: ignore # mutmut generated

mutants_xǁPerformanceGateǁ_emit_otel_event__mutmut['_mutmut_orig'] = PerformanceGate.xǁPerformanceGateǁ_emit_otel_event__mutmut_orig # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_emit_otel_event__mutmut['xǁPerformanceGateǁ_emit_otel_event__mutmut_1'] = PerformanceGate.xǁPerformanceGateǁ_emit_otel_event__mutmut_1 # type: ignore # mutmut generated
mutants_xǁPerformanceGateǁ_emit_otel_event__mutmut['xǁPerformanceGateǁ_emit_otel_event__mutmut_2'] = PerformanceGate.xǁPerformanceGateǁ_emit_otel_event__mutmut_2 # type: ignore # mutmut generated


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
