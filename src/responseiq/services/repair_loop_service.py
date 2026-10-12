# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Bounded, review-first patch validation loop."""

from __future__ import annotations

import hashlib
import re
from enum import Enum
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

from responseiq.services.audit_service import AuditEventType, log_event
from responseiq.services.worktree_service import WorktreeValidationError

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_WORKTREE_PATH = re.compile(r"(?:/tmp/)?responseiq-worktree-[A-Za-z0-9_-]+")


class RepairAttemptStatus(str, Enum):
    STARTED = "started"
    VALIDATED = "validated"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class RepairStopReason(str, Enum):
    VALIDATION_PASSED = "validation_passed"
    ATTEMPT_LIMIT = "attempt_limit"
    REPEATED_PATCH = "repeated_patch"
    REPEATED_FAILURE = "repeated_failure"
    REVISION_UNAVAILABLE = "revision_unavailable"
    REVISION_FAILED = "revision_failed"
    AUDIT_PERSISTENCE_FAILED = "audit_persistence_failed"


class RepairAttempt(BaseModel):
    attempt_number: int = Field(ge=1, le=3)
    patch_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    failure_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    status: RepairAttemptStatus


class RepairLoopResult(BaseModel):
    completed: bool
    review_required: bool = True
    stop_reason: RepairStopReason
    attempts: list[RepairAttempt] = Field(default_factory=list)


Validator = Callable[[str], Awaitable[Any]]
Reviser = Callable[[str, str, int], Awaitable[str | None]]
AttemptRecorder = Callable[[RepairAttempt], Awaitable[bool]]


def patch_fingerprint(patch_text: str) -> str:
    canonical = "\n".join(line.rstrip() for line in patch_text.replace("\r\n", "\n").splitlines()).strip()
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def failure_fingerprint(failure_text: str) -> str:
    normalized = _ANSI_ESCAPE.sub("", failure_text)
    normalized = _WORKTREE_PATH.sub("<worktree>", normalized)
    normalized = " ".join(normalized.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def persist_repair_attempt(incident_id: str, attempt: RepairAttempt) -> bool:
    record = await log_event(
        AuditEventType.REPAIR_ATTEMPT_RECORDED,
        f"Candidate repair attempt {attempt.attempt_number}: {attempt.status.value}",
        incident_id=incident_id,
        outcome=attempt.status.value,
        metadata=attempt.model_dump(mode="json"),
    )
    return record is not None


async def run_bounded_repair_loop(
    *,
    incident_id: str,
    initial_patch: str,
    validate: Validator,
    revise: Reviser | None,
    record_attempt: AttemptRecorder,
    max_attempts: int = 3,
) -> RepairLoopResult:
    """Try at most three candidates, stopping on repeated failures or missing evidence."""
    if not 1 <= max_attempts <= 3:
        raise ValueError("max_attempts must be between 1 and 3")
    if not initial_patch.strip():
        raise ValueError("initial_patch must not be empty")

    attempts: list[RepairAttempt] = []
    seen_patches: dict[str, str | None] = {}
    seen_failures: set[str] = set()
    candidate = initial_patch

    for attempt_number in range(1, max_attempts + 1):
        fingerprint = patch_fingerprint(candidate)
        if fingerprint in seen_patches:
            duplicate = RepairAttempt(
                attempt_number=attempt_number,
                patch_fingerprint=fingerprint,
                failure_fingerprint=seen_patches[fingerprint],
                status=RepairAttemptStatus.DUPLICATE,
            )
            attempts.append(duplicate)
            if not await record_attempt(duplicate):
                return RepairLoopResult(
                    completed=False,
                    stop_reason=RepairStopReason.AUDIT_PERSISTENCE_FAILED,
                    attempts=attempts,
                )
            return RepairLoopResult(
                completed=False,
                stop_reason=RepairStopReason.REPEATED_PATCH,
                attempts=attempts,
            )

        started = RepairAttempt(
            attempt_number=attempt_number,
            patch_fingerprint=fingerprint,
            status=RepairAttemptStatus.STARTED,
        )
        try:
            attempt_started = await record_attempt(started)
        except Exception:
            attempt_started = False
        if not attempt_started:
            return RepairLoopResult(
                completed=False,
                stop_reason=RepairStopReason.AUDIT_PERSISTENCE_FAILED,
                attempts=attempts,
            )

        try:
            await validate(candidate)
        except WorktreeValidationError as exc:
            failure_hash = failure_fingerprint(str(exc))
            attempt = RepairAttempt(
                attempt_number=attempt_number,
                patch_fingerprint=fingerprint,
                failure_fingerprint=failure_hash,
                status=RepairAttemptStatus.FAILED,
            )
            attempts.append(attempt)
            seen_patches[fingerprint] = failure_hash
            if not await record_attempt(attempt):
                return RepairLoopResult(
                    completed=False,
                    stop_reason=RepairStopReason.AUDIT_PERSISTENCE_FAILED,
                    attempts=attempts,
                )
            if failure_hash in seen_failures:
                return RepairLoopResult(
                    completed=False,
                    stop_reason=RepairStopReason.REPEATED_FAILURE,
                    attempts=attempts,
                )
            seen_failures.add(failure_hash)
            if attempt_number == max_attempts:
                return RepairLoopResult(
                    completed=False,
                    stop_reason=RepairStopReason.ATTEMPT_LIMIT,
                    attempts=attempts,
                )
            if revise is None:
                return RepairLoopResult(
                    completed=False,
                    stop_reason=RepairStopReason.REVISION_UNAVAILABLE,
                    attempts=attempts,
                )
            try:
                revised = await revise(candidate, str(exc), attempt_number)
            except Exception:
                return RepairLoopResult(
                    completed=False,
                    stop_reason=RepairStopReason.REVISION_FAILED,
                    attempts=attempts,
                )
            if not revised or not revised.strip():
                return RepairLoopResult(
                    completed=False,
                    stop_reason=RepairStopReason.REVISION_UNAVAILABLE,
                    attempts=attempts,
                )
            candidate = revised
            continue

        attempt = RepairAttempt(
            attempt_number=attempt_number,
            patch_fingerprint=fingerprint,
            status=RepairAttemptStatus.VALIDATED,
        )
        attempts.append(attempt)
        if not await record_attempt(attempt):
            return RepairLoopResult(
                completed=False,
                stop_reason=RepairStopReason.AUDIT_PERSISTENCE_FAILED,
                attempts=attempts,
            )
        return RepairLoopResult(
            completed=True,
            stop_reason=RepairStopReason.VALIDATION_PASSED,
            attempts=attempts,
        )

    return RepairLoopResult(
        completed=False,
        stop_reason=RepairStopReason.ATTEMPT_LIMIT,
        attempts=attempts,
    )
