import json
import subprocess
from pathlib import Path

import pytest

from responseiq.schemas.proof import ContextResolutionReason
from responseiq.utils.artifact_provenance import (
    ArtifactProvenance,
    ProvenanceError,
    ProvenanceRegistry,
    ProvenanceResolver,
)
from responseiq.utils.context_extractor import extract_source_context

DIGEST = "sha256:" + "a" * 64


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    (root / "services" / "payments").mkdir(parents=True)
    (root / "services" / "payments" / "app.py").write_text("def charge():\n    raise ValueError('boom')\n")
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "add", "--all")
    _git(root, "commit", "-m", "initial")
    return root, _git(root, "rev-parse", "HEAD")


def _record(root: Path, commit: str, **kwargs) -> ArtifactProvenance:
    return ArtifactProvenance(
        artifact_digest=DIGEST, repository="acme/payments", commit_sha=commit, source_root=root, **kwargs
    )


def _resolver(record: ArtifactProvenance, digest: str = DIGEST) -> ProvenanceResolver:
    registry = ProvenanceRegistry()
    registry.register(record)
    return ProvenanceResolver(registry, digest)


@pytest.mark.parametrize(
    ("digest", "commit"),
    [("sha256:abc", "a" * 40), (DIGEST, "abc123"), (DIGEST.upper(), "G" * 40)],
)
def test_record_rejects_malformed_identifiers(tmp_path, digest, commit):
    with pytest.raises(ProvenanceError):
        ArtifactProvenance(artifact_digest=digest, repository="r", commit_sha=commit, source_root=tmp_path)


def test_record_normalizes_case(tmp_path):
    record = ArtifactProvenance(
        artifact_digest="SHA256:" + "A" * 64, repository="r", commit_sha="B" * 40, source_root=tmp_path
    )
    assert record.artifact_digest == DIGEST
    assert record.commit_sha == "b" * 40


def test_registry_rejects_conflicting_record(repo):
    root, commit = repo
    registry = ProvenanceRegistry()
    registry.register(_record(root, commit))
    with pytest.raises(ProvenanceError, match="conflicting"):
        registry.register(ArtifactProvenance(DIGEST, "other/repo", commit, root))


def test_registry_allows_idempotent_registration(repo):
    root, commit = repo
    registry = ProvenanceRegistry()
    registry.register(_record(root, commit))
    registry.register(_record(root, commit))
    assert registry.get(DIGEST.upper()) is not None


def test_registry_loads_from_file(repo, tmp_path):
    root, commit = repo
    path = tmp_path / "provenance.json"
    path.write_text(
        json.dumps(
            {
                "artifacts": [
                    {"digest": DIGEST, "repository": "acme/payments", "commit_sha": commit, "source_root": str(root)}
                ]
            }
        )
    )
    assert ProvenanceRegistry.from_file(path).get(DIGEST).commit_sha == commit


@pytest.mark.asyncio
async def test_resolves_container_path_at_matching_commit(repo):
    root, commit = repo
    resolver = _resolver(_record(root, commit, path_prefix="/app"))

    result = await resolver.resolve("/app/services/payments/app.py", 2)

    assert result.ok
    assert result.resolved_path == (root / "services" / "payments" / "app.py").resolve()
    assert result.repo_name == "acme/payments"


@pytest.mark.asyncio
async def test_unknown_artifact_fails_closed(repo):
    root, commit = repo
    resolver = _resolver(_record(root, commit), digest="sha256:" + "b" * 64)

    result = await resolver.resolve("services/payments/app.py", 1)

    assert not result.ok
    assert result.failure.reason == ContextResolutionReason.REPO_NOT_CONFIGURED


@pytest.mark.asyncio
async def test_checkout_at_different_commit_fails_closed(repo):
    root, commit = repo
    (root / "services" / "payments" / "app.py").write_text("def charge():\n    return 1\n")
    _git(root, "commit", "-am", "fix")
    resolver = _resolver(_record(root, commit))

    result = await resolver.resolve("services/payments/app.py", 1)

    assert not result.ok
    assert result.failure.reason == ContextResolutionReason.PROVENANCE_MISMATCH
    assert commit in result.failure.detail


@pytest.mark.asyncio
async def test_non_git_source_root_fails_closed(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n")
    resolver = _resolver(_record(tmp_path, "c" * 40))

    result = await resolver.resolve("app.py", 1)

    assert not result.ok
    assert result.failure.reason == ContextResolutionReason.PROVENANCE_MISMATCH


@pytest.mark.asyncio
@pytest.mark.parametrize("escape", ["../outside.py", "/app/../../outside.py", "services/../../outside.py"])
async def test_path_traversal_cannot_escape_source_root(repo, tmp_path, escape):
    root, commit = repo
    (tmp_path / "outside.py").write_text("secret = 1\n")
    resolver = _resolver(_record(root, commit, path_prefix="/app"))

    result = await resolver.resolve(escape, 1)

    assert not result.ok
    assert result.failure.reason == ContextResolutionReason.FILE_NOT_FOUND


@pytest.mark.asyncio
async def test_symlink_escape_is_rejected(repo, tmp_path):
    root, commit = repo
    (tmp_path / "outside.py").write_text("secret = 1\n")
    (root / "link.py").symlink_to(tmp_path / "outside.py")
    _git(root, "add", "link.py")
    _git(root, "commit", "-m", "symlink")
    resolver = _resolver(_record(root, _git(root, "rev-parse", "HEAD")))

    result = await resolver.resolve("link.py", 1)

    assert not result.ok


@pytest.mark.asyncio
async def test_extractor_uses_provenance_resolver_and_records_failures(repo):
    root, commit = repo
    resolver = _resolver(_record(root, commit, path_prefix="/app"))

    context = await extract_source_context('File "/app/services/payments/app.py", line 2, in charge', resolver=resolver)
    assert "raise ValueError('boom')" in context.rendered
    assert context.failures == []

    stale = _resolver(_record(root, "d" * 40, path_prefix="/app"))
    missing = await extract_source_context(
        'File "/app/services/payments/app.py", line 2, in charge', root_path=root / "nowhere", resolver=stale
    )
    assert missing.rendered == ""
    assert missing.failures[0].reason == ContextResolutionReason.PROVENANCE_MISMATCH
