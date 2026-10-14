import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from responseiq.schemas.proof import ContextResolutionReason
from responseiq.utils.artifact_provenance import (
    ArtifactProvenance,
    ProvenanceError,
    ProvenanceRegistry,
    ProvenanceResolver,
    SigstoreProvenanceVerifier,
    persist_verified_provenance,
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
async def test_dirty_checkout_fails_closed(repo):
    root, commit = repo
    resolver = _resolver(_record(root, commit))
    (root / "services" / "payments" / "app.py").write_text("def charge():\n    return 1\n")

    result = await resolver.resolve("services/payments/app.py", 2)

    assert not result.ok
    assert result.failure.reason == ContextResolutionReason.PROVENANCE_MISMATCH


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


def _verifier_fixture(commit: str, *, digest: str = DIGEST, repository: str = "acme/payments"):
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": "image", "digest": {"sha256": digest.removeprefix("sha256:")}}],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "resolvedDependencies": [
                    {
                        "uri": f"git+https://github.com/{repository}@refs/heads/main",
                        "digest": {"gitCommit": commit},
                    }
                ]
            }
        },
    }

    class FakeVerifier:
        def __init__(self):
            self.policy = None

        def verify_dsse(self, bundle, policy):
            self.policy = policy
            return "application/vnd.in-toto+json", json.dumps(statement).encode()

    backend = FakeVerifier()
    verifier = SigstoreProvenanceVerifier(
        "https://github.com/acme/payments/.github/workflows/build.yml@refs/heads/main",
        verifier=backend,
        bundle_loader=lambda raw: raw,
        identity_policy_factory=lambda identity, issuer: (identity, issuer),
    )
    return verifier, backend


def test_sigstore_verifier_requires_configured_identity_and_matching_slsa(repo):
    root, commit = repo
    verifier, backend = _verifier_fixture(commit)

    record, bundle_sha, predicate_type = verifier.verify(b"signed-bundle", DIGEST, "acme/payments", root)

    assert record.commit_sha == commit
    assert record.repository == "acme/payments"
    assert backend.policy == (
        "https://github.com/acme/payments/.github/workflows/build.yml@refs/heads/main",
        "https://token.actions.githubusercontent.com",
    )
    assert bundle_sha == hashlib.sha256(b"signed-bundle").hexdigest()
    assert predicate_type == "https://slsa.dev/provenance/v1"


@pytest.mark.parametrize(
    ("requested_digest", "repository"),
    [("sha256:" + "b" * 64, "acme/payments"), (DIGEST, "acme/other")],
)
def test_sigstore_verifier_rejects_wrong_artifact_subject_or_repository(repo, requested_digest, repository):
    root, commit = repo
    verifier, _ = _verifier_fixture(commit)

    with pytest.raises(ProvenanceError):
        verifier.verify(b"signed-bundle", requested_digest, repository, root)


def test_sigstore_verifier_rejects_failed_signature(repo):
    root, commit = repo
    verifier, _ = _verifier_fixture(commit)

    class RejectingVerifier:
        def verify_dsse(self, bundle, policy):
            raise ValueError("untrusted signer")

    verifier._verifier = RejectingVerifier()
    with pytest.raises(ProvenanceError, match="DSSE verification failed"):
        verifier.verify(b"unsigned", DIGEST, "acme/payments", root)


def test_persists_verified_provenance_idempotently_and_loads_it(repo):
    root, commit = repo
    verifier, _ = _verifier_fixture(commit)
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        stored = persist_verified_provenance(session, verifier, b"signed-bundle", DIGEST, "acme/payments", root)
        assert persist_verified_provenance(session, verifier, b"signed-bundle", DIGEST, "acme/payments", root) == stored
        session.commit()
        registry = ProvenanceRegistry.from_session(session)

    assert registry.get(DIGEST).commit_sha == commit
    assert stored.bundle_sha256 == hashlib.sha256(b"signed-bundle").hexdigest()
    assert stored.bundle_json == "signed-bundle"


def test_conflicting_verified_provenance_is_rejected(repo):
    root, commit = repo
    verifier, _ = _verifier_fixture(commit)
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        persist_verified_provenance(session, verifier, b"signed-bundle", DIGEST, "acme/payments", root)
        conflicting, _ = _verifier_fixture(commit)
        conflicting.signer_identity = "different-trusted-identity"
        with pytest.raises(ProvenanceError, match="conflicting"):
            persist_verified_provenance(session, conflicting, b"signed-bundle", DIGEST, "acme/payments", root)


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


@pytest.mark.asyncio
async def test_required_provenance_never_falls_back_to_local_resolution(repo):
    root, _ = repo
    stale = _resolver(_record(root, "d" * 40, path_prefix="/app"))

    context = await extract_source_context(
        'File "/app/services/payments/app.py", line 2, in charge',
        root_path=root,
        resolver=stale,
        require_resolver=True,
    )

    assert context.rendered == ""
    assert context.failures[0].reason == ContextResolutionReason.PROVENANCE_MISMATCH
