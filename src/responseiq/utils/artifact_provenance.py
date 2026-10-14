# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Artifact-to-source provenance registry.

Binds a runtime artifact digest to the exact repository commit it was built
from, so stack-trace paths resolve against the source that actually ran.
Unknown artifacts, checkout/commit mismatches, and path escapes fail closed.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
import subprocess  # nosec B404
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlsplit

from sqlmodel import Session, select

from responseiq.models.base import ArtifactProvenanceRecord
from responseiq.schemas.proof import ContextResolutionFailure, ContextResolutionReason
from responseiq.utils.multi_repo_resolver import ResolutionResult

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_SLSA_V1 = "https://slsa.dev/provenance/v1"
_IN_TOTO_STATEMENT_V1 = "https://in-toto.io/Statement/v1"
_DSSE_PAYLOAD_TYPE = "application/vnd.in-toto+json"
_GITHUB_OIDC_ISSUER = "https://token.actions.githubusercontent.com"


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

    @classmethod
    def from_session(cls, session: Session, artifact_digest: Optional[str] = None) -> "ProvenanceRegistry":
        registry = cls()
        query = select(ArtifactProvenanceRecord)
        if artifact_digest:
            query = query.where(ArtifactProvenanceRecord.artifact_digest == artifact_digest.strip().lower())
        for item in session.exec(query).all():
            registry.register(
                ArtifactProvenance(
                    artifact_digest=item.artifact_digest,
                    repository=item.repository,
                    commit_sha=item.commit_sha,
                    source_root=Path(item.source_root),
                    path_prefix=item.path_prefix,
                )
            )
        return registry


class SigstoreProvenanceVerifier:
    """Verifies signed SLSA provenance before it can enter persistent storage."""

    def __init__(
        self,
        signer_identity: str,
        signer_issuer: str = _GITHUB_OIDC_ISSUER,
        *,
        verifier: Any = None,
        bundle_loader: Optional[Callable[[bytes], Any]] = None,
        identity_policy_factory: Optional[Callable[[str, str], Any]] = None,
    ) -> None:
        if not signer_identity.strip() or not signer_issuer.strip():
            raise ProvenanceError("trusted signer identity and OIDC issuer are required")
        self.signer_identity = signer_identity
        self.signer_issuer = signer_issuer
        self._verifier = verifier
        self._bundle_loader = bundle_loader
        self._identity_policy_factory = identity_policy_factory

    def verify(
        self,
        bundle_json: bytes,
        artifact_digest: str,
        repository: str,
        source_root: Path,
        path_prefix: str = "",
    ) -> tuple[ArtifactProvenance, str, str]:
        digest = artifact_digest.strip().lower()
        if not _DIGEST_RE.fullmatch(digest):
            raise ProvenanceError("artifact_digest must be 'sha256:' followed by 64 hex characters")
        if len(bundle_json) > 10 * 1024 * 1024:
            raise ProvenanceError("Sigstore bundle exceeds the 10 MiB limit")

        verifier, bundle_loader, policy_factory = self._verification_components()
        try:
            bundle = bundle_loader(bundle_json)
            payload_type, payload = verifier.verify_dsse(
                bundle,
                policy_factory(self.signer_identity, self.signer_issuer),
            )
        except Exception as exc:
            raise ProvenanceError(f"Sigstore DSSE verification failed: {exc}") from exc
        if payload_type != _DSSE_PAYLOAD_TYPE:
            raise ProvenanceError("Sigstore DSSE payload is not an in-toto statement")

        try:
            statement = json.loads(payload)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProvenanceError("verified DSSE payload is not valid JSON") from exc

        commit_sha = _validate_slsa_statement(statement, digest, repository)
        record = ArtifactProvenance(
            artifact_digest=digest,
            repository=repository,
            commit_sha=commit_sha,
            source_root=Path(source_root),
            path_prefix=path_prefix,
        )
        bundle_sha256 = hashlib.sha256(bundle_json).hexdigest()
        return record, bundle_sha256, _SLSA_V1

    def _verification_components(self) -> tuple[Any, Callable[[bytes], Any], Callable[[str, str], Any]]:
        if self._verifier is not None and self._bundle_loader and self._identity_policy_factory:
            return self._verifier, self._bundle_loader, self._identity_policy_factory
        try:
            from sigstore.models import Bundle
            from sigstore.verify import Verifier, policy
        except ImportError as exc:
            raise ProvenanceError("Sigstore support is unavailable; install responseiq[provenance]") from exc
        verifier = self._verifier or Verifier.production()
        bundle_loader = self._bundle_loader or Bundle.from_json
        policy_factory = self._identity_policy_factory or (
            lambda identity, issuer: policy.Identity(identity=identity, issuer=issuer)
        )
        return verifier, bundle_loader, policy_factory


def persist_verified_provenance(
    session: Session,
    verifier: SigstoreProvenanceVerifier,
    bundle_json: bytes,
    artifact_digest: str,
    repository: str,
    source_root: Path,
    path_prefix: str = "",
) -> ArtifactProvenanceRecord:
    record, bundle_sha256, predicate_type = verifier.verify(
        bundle_json, artifact_digest, repository, source_root, path_prefix
    )
    actual_head = _head_sha(record.source_root)
    if actual_head != record.commit_sha or not _working_tree_clean(record.source_root):
        raise ProvenanceError("source checkout must be clean and at the signed SLSA commit")

    existing = session.get(ArtifactProvenanceRecord, record.artifact_digest)
    if existing is not None:
        if (
            existing.repository == record.repository
            and existing.commit_sha == record.commit_sha
            and Path(existing.source_root) == record.source_root
            and existing.path_prefix == record.path_prefix
            and existing.signer_identity == verifier.signer_identity
            and existing.signer_issuer == verifier.signer_issuer
            and existing.bundle_sha256 == bundle_sha256
        ):
            return existing
        raise ProvenanceError(f"conflicting verified provenance already stored for {record.artifact_digest}")

    stored = ArtifactProvenanceRecord(
        artifact_digest=record.artifact_digest,
        repository=record.repository,
        commit_sha=record.commit_sha,
        source_root=str(record.source_root),
        path_prefix=record.path_prefix,
        signer_identity=verifier.signer_identity,
        signer_issuer=verifier.signer_issuer,
        bundle_sha256=bundle_sha256,
        bundle_json=bundle_json.decode("utf-8"),
        predicate_type=predicate_type,
    )
    session.add(stored)
    session.flush()
    return stored


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
        clean = await asyncio.to_thread(_working_tree_clean, record.source_root)
        if head != record.commit_sha or not clean:
            return _failure(
                path_str,
                line_num,
                ContextResolutionReason.PROVENANCE_MISMATCH,
                f"Checkout HEAD {head or 'unknown'} must match recorded commit {record.commit_sha} and be clean.",
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


def _working_tree_clean(source_root: Path) -> bool:
    git_bin = shutil.which("git")
    if git_bin is None:
        return False

    try:
        result = subprocess.run(  # noqa: S603
            [git_bin, "-C", str(source_root), "status", "--porcelain", "--untracked-files=all"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return not result.stdout.strip()


def _validate_slsa_statement(statement: Any, artifact_digest: str, repository: str) -> str:
    if not isinstance(statement, dict):
        raise ProvenanceError("SLSA statement must be a JSON object")
    if statement.get("_type") != _IN_TOTO_STATEMENT_V1:
        raise ProvenanceError("unsupported in-toto statement type")
    if statement.get("predicateType") != _SLSA_V1:
        raise ProvenanceError("only SLSA provenance v1 is accepted")

    expected_hex_digest = artifact_digest.removeprefix("sha256:")
    subjects = statement.get("subject")
    if not isinstance(subjects, list) or not any(
        isinstance(subject, dict)
        and isinstance(subject.get("digest"), dict)
        and subject["digest"].get("sha256") == expected_hex_digest
        for subject in subjects
    ):
        raise ProvenanceError("SLSA subject does not match the requested artifact digest")

    build_definition = statement.get("predicate", {}).get("buildDefinition", {})
    dependencies = build_definition.get("resolvedDependencies")
    if not isinstance(dependencies, list):
        raise ProvenanceError("SLSA provenance has no resolved dependencies")

    expected_repository = _normalize_repository(repository)
    commits = set()
    for dependency in dependencies:
        if not isinstance(dependency, dict) or _normalize_repository(dependency.get("uri", "")) != expected_repository:
            continue
        digest = dependency.get("digest")
        if isinstance(digest, dict) and isinstance(digest.get("gitCommit"), str):
            commits.add(digest["gitCommit"].lower())
    if len(commits) != 1 or not _COMMIT_RE.fullmatch(next(iter(commits), "")):
        raise ProvenanceError("SLSA provenance must identify one full Git commit for the expected repository")
    return next(iter(commits))


def _normalize_repository(value: str) -> str:
    normalized = value.strip()
    if normalized.startswith("git+"):
        normalized = normalized[4:]
    if "://" in normalized:
        parsed = urlsplit(normalized)
        normalized = parsed.path if parsed.netloc.lower() == "github.com" else f"{parsed.netloc}{parsed.path}"
    normalized = normalized.split("@", 1)[0].removesuffix(".git").strip("/")
    return normalized.lower()


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
