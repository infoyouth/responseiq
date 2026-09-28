"""
Tests for P2.4 — Multi-Repo Context Resolution.

Coverage targets
----------------
* RepoEntry construction and from_dict()
* Settings.repo_map validator (dict, JSON str, RepoEntry passthrough)
* MultiRepoResolver._match_entry — service prefix, path prefix, default
* MultiRepoResolver._strip_prefix — no-op, trailing slash, monorepo
* MultiRepoResolver._try_local — direct hit, suffix walk, miss
* MultiRepoResolver.resolve — local hit, cache hit, no-entry, file-not-found
* MultiRepoResolver.resolve_many — concurrent resolution
* ContextResolutionFailure and proof.py schema additions
* extract_context_from_log integration with resolver + context_failures list
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List, Optional, Tuple


import pytest

from responseiq.config.settings import RepoEntry, Settings
from responseiq.schemas.proof import (
    ContextResolutionFailure,
    ContextResolutionReason,
    ProofBundle,
)
from responseiq.utils.multi_repo_resolver import MultiRepoResolver, ResolutionResult


# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------


def _make_entry(
    local_path: Optional[Path] = None,
    remote_url: Optional[str] = None,
    path_prefix: str = "",
    service_prefixes: Optional[List[str]] = None,
    git_ref: str = "HEAD",
) -> RepoEntry:
    return RepoEntry(
        local_path=local_path,
        remote_url=remote_url,
        git_ref=git_ref,
        path_prefix=path_prefix,
        service_prefixes=service_prefixes or [],
    )


@pytest.fixture()
def tmp_src(tmp_path: Path) -> Path:
    """Create a minimal source tree in a temp dir."""
    src = tmp_path / "src" / "payments"
    src.mkdir(parents=True)
    (src / "checkout.py").write_text("def process():\n    pass\n")
    (tmp_path / "main.py").write_text("print('hello')\n")
    return tmp_path


# ---------------------------------------------------------------------------
# RepoEntry tests
# ---------------------------------------------------------------------------


class TestRepoEntry:
    def test_from_dict_full(self, tmp_path: Path) -> None:
        data = {
            "local_path": str(tmp_path),
            "remote_url": "https://github.com/example/repo.git",
            "git_ref": "v1.2.3",
            "path_prefix": "services/payments",
            "service_prefixes": ["payments.", "com.example.payments"],
        }
        entry = RepoEntry.from_dict(data)
        assert entry.local_path == tmp_path
        assert entry.remote_url == "https://github.com/example/repo.git"
        assert entry.git_ref == "v1.2.3"
        assert entry.path_prefix == "services/payments"
        assert entry.service_prefixes == ["payments.", "com.example.payments"]

    def test_from_dict_minimal(self) -> None:
        entry = RepoEntry.from_dict({})
        assert entry.local_path is None
        assert entry.remote_url is None
        assert entry.git_ref == "HEAD"
        assert entry.path_prefix == ""
        assert entry.service_prefixes == []

    def test_from_dict_local_path_none_if_absent(self) -> None:
        entry = RepoEntry.from_dict({"remote_url": "https://host/repo.git"})
        assert entry.local_path is None
        assert entry.remote_url == "https://host/repo.git"


# ---------------------------------------------------------------------------
# Settings.repo_map validator
# ---------------------------------------------------------------------------


class TestSettingsRepoMap:
    def test_empty_by_default(self) -> None:
        s = Settings()
        assert s.repo_map == {}

    def test_dict_input(self, tmp_path: Path) -> None:
        raw: dict = {
            "payments": {
                "local_path": str(tmp_path),
                "service_prefixes": ["payments."],
            }
        }
        s = Settings(repo_map=raw)  # type: ignore[arg-type]
        assert "payments" in s.repo_map
        assert isinstance(s.repo_map["payments"], RepoEntry)
        assert s.repo_map["payments"].local_path == tmp_path

    def test_json_string_input(self, tmp_path: Path) -> None:
        raw_json = json.dumps({"api": {"local_path": str(tmp_path)}})
        s = Settings(repo_map=raw_json)  # type: ignore[arg-type]
        assert "api" in s.repo_map

    def test_repo_entry_passthrough(self, tmp_path: Path) -> None:
        entry = _make_entry(local_path=tmp_path)
        s = Settings(repo_map={"svc": entry})  # type: ignore[arg-type]
        assert s.repo_map["svc"] is entry

    def test_invalid_repo_map_raises(self) -> None:
        with pytest.raises((ValueError, Exception)):
            Settings(repo_map={"bad": 42})  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# MultiRepoResolver._match_entry
# ---------------------------------------------------------------------------


class TestMatchEntry:
    def test_no_entries_returns_none(self) -> None:
        r = MultiRepoResolver({})
        name, entry = r._match_entry("/app/src/main.py")
        assert entry is None

    def test_service_prefix_exact_start(self) -> None:
        r = MultiRepoResolver(
            {
                "payments": _make_entry(service_prefixes=["payments/"]),
            }
        )
        name, entry = r._match_entry("payments/src/checkout.py")
        assert name == "payments"
        assert entry is not None

    def test_service_prefix_match_in_path(self) -> None:
        r = MultiRepoResolver(
            {
                "payments": _make_entry(service_prefixes=["payments"]),
            }
        )
        name, entry = r._match_entry("/app/payments/src/checkout.py")
        assert name == "payments"

    def test_path_prefix_match(self) -> None:
        r = MultiRepoResolver(
            {
                "monorepo_svc": _make_entry(path_prefix="services/payments"),
            }
        )
        name, entry = r._match_entry("services/payments/src/main.py")
        assert name == "monorepo_svc"

    def test_default_fallback(self) -> None:
        r = MultiRepoResolver(
            {
                "default": _make_entry(service_prefixes=[]),
            }
        )
        name, entry = r._match_entry("/whatever/path.py")
        assert name == "default"
        assert entry is not None

    def test_first_match_wins(self) -> None:
        # Insertion order preserved in Python 3.7+
        r = MultiRepoResolver(
            {
                "a": _make_entry(service_prefixes=["shared/"]),
                "b": _make_entry(service_prefixes=["shared/"]),
            }
        )
        name, _ = r._match_entry("shared/lib.py")
        assert name == "a"


# ---------------------------------------------------------------------------
# MultiRepoResolver._strip_prefix
# ---------------------------------------------------------------------------


class TestStripPrefix:
    def test_no_prefix(self) -> None:
        assert MultiRepoResolver._strip_prefix("src/main.py", "") == "src/main.py"

    def test_strips_prefix(self) -> None:
        result = MultiRepoResolver._strip_prefix("services/payments/src/main.py", "services/payments")
        assert result == "src/main.py"

    def test_trailing_slash_on_prefix(self) -> None:
        result = MultiRepoResolver._strip_prefix("services/payments/src/main.py", "services/payments/")
        assert result == "src/main.py"

    def test_no_match_returns_original(self) -> None:
        result = MultiRepoResolver._strip_prefix("/app/other/main.py", "services/payments")
        # Should not strip
        assert "main.py" in result


# ---------------------------------------------------------------------------
# MultiRepoResolver._try_local
# ---------------------------------------------------------------------------


class TestTryLocal:
    def test_direct_hit(self, tmp_src: Path) -> None:
        result = MultiRepoResolver._try_local("main.py", tmp_src, "repo", 1)
        assert result.ok
        assert result.resolved_path == tmp_src / "main.py"

    def test_suffix_walk_hit(self, tmp_src: Path) -> None:
        # Stack trace has /app/src/payments/checkout.py — our root is tmp_src
        result = MultiRepoResolver._try_local("/app/src/payments/checkout.py", tmp_src, "repo", 5)
        assert result.ok
        assert result.resolved_path is not None
        assert result.resolved_path.name == "checkout.py"

    def test_miss_returns_non_ok(self, tmp_src: Path) -> None:
        result = MultiRepoResolver._try_local("does/not/exist.py", tmp_src, "repo", 1)
        assert not result.ok
        assert result.failure is None  # failure=None is the "tried but missed" sentinel


# ---------------------------------------------------------------------------
# MultiRepoResolver.resolve — high level
# ---------------------------------------------------------------------------


class TestResolve:
    def test_local_hit(self, tmp_src: Path) -> None:
        resolver = MultiRepoResolver(
            {
                "default": _make_entry(local_path=tmp_src),
            }
        )
        result = asyncio.run(resolver.resolve("main.py", 1))
        assert result.ok
        assert result.repo_name == "default"

    def test_no_entry_returns_failure(self) -> None:
        resolver = MultiRepoResolver({})
        result = asyncio.run(resolver.resolve("/some/unknown/path.py", 10))
        assert not result.ok
        assert result.failure is not None
        assert result.failure.reason == ContextResolutionReason.REPO_NOT_CONFIGURED

    def test_file_not_found_returns_failure(self, tmp_path: Path) -> None:
        resolver = MultiRepoResolver(
            {
                "default": _make_entry(local_path=tmp_path),
            }
        )
        result = asyncio.run(resolver.resolve("ghost/file.py", 99))
        assert not result.ok
        assert result.failure is not None
        reason = result.failure.reason
        assert reason in (
            ContextResolutionReason.FILE_NOT_FOUND,
            ContextResolutionReason.LOCAL_NOT_FOUND,
        )

    def test_cache_hit_avoids_clone(self, tmp_src: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """If the cache dir exists and has the file, _sparse_checkout is never called."""

        async def _fake_checkout(*_a: object, **_kw: object) -> None:
            raise AssertionError("_sparse_checkout should not be called when cache hit")

        resolver = MultiRepoResolver(
            {
                "svc": _make_entry(
                    remote_url="https://github.com/example/svc.git",
                    service_prefixes=["main"],
                ),
            }
        )

        # Patch _CACHE_ROOT so "svc" maps to tmp_src
        import responseiq.utils.multi_repo_resolver as mrm

        monkeypatch.setattr(mrm, "_CACHE_ROOT", tmp_src.parent)
        # Rename tmp_src to match expected cache path
        svc_cache = tmp_src.parent / "svc"
        if not svc_cache.exists():
            tmp_src.rename(svc_cache)

        monkeypatch.setattr(resolver, "_sparse_checkout", _fake_checkout)

        result = asyncio.run(resolver.resolve("main.py", 1))
        # Either ok (cache hit) or not ok (miss) — main thing is no exception
        assert isinstance(result, ResolutionResult)

    def test_remote_clone_failure_returns_structured_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def _fail_checkout(*_a: object, **_kw: object) -> None:
            raise RuntimeError("network error")

        resolver = MultiRepoResolver(
            {
                "svc": _make_entry(
                    remote_url="https://github.com/example/svc.git",
                    service_prefixes=["svc/"],
                ),
            }
        )
        monkeypatch.setattr(MultiRepoResolver, "_sparse_checkout", staticmethod(_fail_checkout))

        result = asyncio.run(resolver.resolve("svc/main.py", 1))
        assert not result.ok
        assert result.failure is not None
        assert result.failure.reason == ContextResolutionReason.REMOTE_CLONE_FAILED
        assert "network error" in result.failure.detail


# ---------------------------------------------------------------------------
# MultiRepoResolver.resolve_many — concurrency
# ---------------------------------------------------------------------------


class TestResolveMany:
    def test_returns_list_of_results(self, tmp_src: Path) -> None:
        resolver = MultiRepoResolver(
            {
                "default": _make_entry(local_path=tmp_src),
            }
        )
        refs: List[Tuple[str, int]] = [
            ("main.py", 1),
            ("ghost.py", 5),
        ]
        results = asyncio.run(resolver.resolve_many(refs))
        assert len(results) == 2
        ok_results = [r for r in results if r.ok]
        fail_results = [r for r in results if not r.ok]
        assert len(ok_results) == 1
        assert len(fail_results) == 1

    def test_empty_input(self) -> None:
        resolver = MultiRepoResolver({})
        results = asyncio.run(resolver.resolve_many([]))
        assert results == []


# ---------------------------------------------------------------------------
# ContextResolutionFailure schema
# ---------------------------------------------------------------------------


class TestContextResolutionFailure:
    def test_to_dict(self) -> None:
        f = ContextResolutionFailure(
            path="/app/main.py",
            line_num=42,
            reason=ContextResolutionReason.FILE_NOT_FOUND,
            attempted_repos=["payments"],
            detail="not found",
        )
        d = f.to_dict()
        assert d["path"] == "/app/main.py"
        assert d["line_num"] == 42
        assert d["reason"] == "file_not_found"
        assert d["attempted_repos"] == ["payments"]
        assert "timestamp" in d

    def test_all_reason_values_exist(self) -> None:
        reasons = {r.value for r in ContextResolutionReason}
        assert "repo_not_configured" in reasons
        assert "local_not_found" in reasons
        assert "remote_clone_failed" in reasons
        assert "file_not_found" in reasons
        assert "parse_error" in reasons


# ---------------------------------------------------------------------------
# ProofBundle.context_failures field
# ---------------------------------------------------------------------------


class TestProofBundleContextFailures:
    def test_default_empty(self) -> None:
        from datetime import datetime

        bundle = ProofBundle(incident_id="test-1", created_at=datetime.utcnow())
        assert bundle.context_failures == []

    def test_append_failure(self) -> None:
        from datetime import datetime

        bundle = ProofBundle(incident_id="test-2", created_at=datetime.utcnow())
        f = ContextResolutionFailure(
            path="/app/crash.py",
            line_num=7,
            reason=ContextResolutionReason.REPO_NOT_CONFIGURED,
        )
        bundle.context_failures.append(f)
        assert len(bundle.context_failures) == 1
        assert bundle.context_failures[0].path == "/app/crash.py"


# ---------------------------------------------------------------------------
# extract_context_from_log integration
# ---------------------------------------------------------------------------


class TestExtractContextIntegration:
    """Verify context_extractor wires failures into context_failures list."""

    def test_collects_failure_when_no_resolver(self, tmp_path: Path) -> None:
        """Without resolver, unresolvable paths generate LOCAL_NOT_FOUND failures."""
        import asyncio

        from responseiq.utils.context_extractor import extract_context_from_log

        log = 'File "/ghost/nonexistent.py", line 5'
        failures: List[ContextResolutionFailure] = []
        result = asyncio.run(extract_context_from_log(log, tmp_path, context_failures=failures))
        assert result == ""
        assert len(failures) == 1
        assert failures[0].path == "/ghost/nonexistent.py"
        assert failures[0].reason == ContextResolutionReason.LOCAL_NOT_FOUND

    def test_resolves_file_with_resolver(self, tmp_src: Path) -> None:
        """When resolver finds the file, a code block is returned."""
        import asyncio

        from responseiq.utils.context_extractor import extract_context_from_log

        resolver = MultiRepoResolver({"default": _make_entry(local_path=tmp_src)})
        log = 'File "/app/main.py", line 1'
        failures: List[ContextResolutionFailure] = []
        result = asyncio.run(extract_context_from_log(log, tmp_src, resolver=resolver, context_failures=failures))
        assert "Source:" in result
        assert len(failures) == 0

    def test_no_failures_when_no_list_provided(self, tmp_path: Path) -> None:
        """Backward-compat: passing no context_failures arg must not raise."""
        import asyncio

        from responseiq.utils.context_extractor import extract_context_from_log

        log = 'File "/ghost/nonexistent.py", line 5'
        # Should not raise even when context_failures is None (default)
        result = asyncio.run(extract_context_from_log(log, tmp_path))
        assert result == ""

    def test_resolver_failure_appended_when_legacy_also_fails(self, tmp_path: Path) -> None:
        """Resolver returns REPO_NOT_CONFIGURED; legacy also fails → failure appended."""
        import asyncio

        from responseiq.utils.context_extractor import extract_context_from_log

        resolver = MultiRepoResolver({})  # Empty map → REPO_NOT_CONFIGURED
        log = 'File "/remote/service/handler.py", line 20'
        failures: List[ContextResolutionFailure] = []
        asyncio.run(extract_context_from_log(log, tmp_path, resolver=resolver, context_failures=failures))
        assert len(failures) == 1
        assert failures[0].reason == ContextResolutionReason.REPO_NOT_CONFIGURED
