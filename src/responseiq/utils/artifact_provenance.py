# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Artifact-to-source provenance registry.

Binds a runtime artifact digest to the exact repository commit it was built
from, so stack-trace paths resolve against the source that actually ran.
Unknown artifacts, checkout/commit mismatches, and path escapes fail closed.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess  # nosec B404
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from responseiq.schemas.proof import ContextResolutionFailure, ContextResolutionReason
from responseiq.utils.multi_repo_resolver import ResolutionResult

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class ProvenanceError(ValueError):
    """Raised when a provenance record is malformed."""


@dataclass(frozen=True)
class ArtifactProvenance:
    """Build provenance for one runtime artifact."""

    artifact_digest: str
    repository: str
    commit_sha: str
    source_root: Path
    path_prefix: str = ""

    def __post_init__(self) -> None:
        digest = self.artifact_digest.strip().lower()
        commit = self.commit_sha.strip().lower()
        if not _DIGEST_RE.match(digest):
            raise ProvenanceError("artifact_digest must be 'sha256:' followed by 64 hex characters")
        if not _COMMIT_RE.match(commit):
            raise ProvenanceError("commit_sha must be a full 40-character lowercase hex SHA")
        if not self.repository.strip():
            raise ProvenanceError("repository is required")
        object.__setattr__(self, "artifact_digest", digest)
        object.__setattr__(self, "commit_sha", commit)
        object.__setattr__(self, "source_root", Path(self.source_root))


class ProvenanceRegistry:
    """In-memory registry of artifact provenance records keyed by digest."""

    def __init__(self) -> None:
        self._records: Dict[str, ArtifactProvenance] = {}

    def register(self, record: ArtifactProvenance) -> None:
        existing = self._records.get(record.artifact_digest)
        if existing is not None and existing != record:
            raise ProvenanceError(f"conflicting provenance already registered for {record.artifact_digest}")
        self._records[record.artifact_digest] = record

    def get(self, artifact_digest: str) -> Optional[ArtifactProvenance]:
        return self._records.get(artifact_digest.strip().lower())

    @classmethod
    def from_file(cls, path: Path) -> "ProvenanceRegistry":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        registry = cls()
        for item in data.get("artifacts", []):
            registry.register(
                ArtifactProvenance(
                    artifact_digest=item["digest"],
                    repository=item["repository"],
                    commit_sha=item["commit_sha"],
                    source_root=Path(item["source_root"]),
                    path_prefix=item.get("path_prefix", ""),
                )
            )
        return registry


class ProvenanceResolver:
    """Resolver for one artifact, interchangeable with ``MultiRepoResolver``."""

    def __init__(self, registry: ProvenanceRegistry, artifact_digest: str) -> None:
        self._registry = registry
        self._digest = artifact_digest

    async def resolve(self, path_str: str, line_num: int) -> ResolutionResult:
        record = self._registry.get(self._digest)
        if record is None:
            return _failure(
                path_str, line_num, ContextResolutionReason.REPO_NOT_CONFIGURED, "No provenance for this artifact."
            )

        head = await asyncio.to_thread(_head_sha, record.source_root)
        if head != record.commit_sha:
            return _failure(
                path_str,
                line_num,
                ContextResolutionReason.PROVENANCE_MISMATCH,
                f"Checkout HEAD {head or 'unknown'} does not match recorded commit {record.commit_sha}.",
                [record.repository],
            )

        resolved = _locate(record, path_str)
        if resolved is None:
            return _failure(
                path_str,
                line_num,
                ContextResolutionReason.FILE_NOT_FOUND,
                "File not found within the verified source root.",
                [record.repository],
            )
        return ResolutionResult(
            path_str=path_str, line_num=line_num, resolved_path=resolved, repo_name=record.repository
        )


def _head_sha(source_root: Path) -> Optional[str]:
    git_bin = shutil.which("git")
    if git_bin is None:
        return None

    try:
        result = subprocess.run(  # noqa: S603
            [git_bin, "-C", str(source_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip().lower() or None


def _locate(record: ArtifactProvenance, path_str: str) -> Optional[Path]:
    relative = path_str.replace("\\", "/")
    prefix = record.path_prefix.replace("\\", "/").strip("/")
    stripped = relative.lstrip("/")
    if prefix and stripped.startswith(prefix + "/"):
        stripped = stripped[len(prefix) + 1 :]

    root = record.source_root.resolve()
    candidate = (root / stripped).resolve()
    if candidate.is_file() and candidate.is_relative_to(root):
        return candidate
    return None


def _failure(
    path_str: str,
    line_num: int,
    reason: ContextResolutionReason,
    detail: str,
    attempted: Optional[list[str]] = None,
) -> ResolutionResult:
    return ResolutionResult(
        path_str=path_str,
        line_num=line_num,
        failure=ContextResolutionFailure(
            path=path_str,
            line_num=line_num,
            reason=reason,
            attempted_repos=attempted or [],
            detail=detail,
            timestamp=datetime.now(timezone.utc),
        ),
    )
