"""
P2.4 — Multi-Repo Context Resolution
======================================
Resolves stack-trace file paths across multiple repositories so the LLM
always receives the exact source that crashed — even when that source lives
in a different repo or a different git commit.

Resolution order
----------------
1. **Local path** — ``repo_map[name].local_path`` is present and the file
   exists there.
2. **Sparse checkout** — ``repo_map[name].remote_url`` is present; the repo
   is cloned/fetched into
   ``~/.cache/responseiq/repos/<name>/`` at ``git_ref`` and the file is
   looked up inside that tree.
3. **Graceful failure** — a ``ContextResolutionFailure`` is returned instead
   of raising; the caller decides whether to surface it in the prompt.

Monorepo support
----------------
Set ``path_prefix`` on a ``RepoEntry`` to strip a leading path component.
E.g. if paths in the stack trace start with ``services/payments/src/..``
and the repo root *is* ``services/payments/``, set
``path_prefix = "services/payments"``.

Service-prefix matching
-----------------------
``service_prefixes`` is a list of strings (module names, package prefixes,
path fragments) that identify which ``RepoEntry`` owns an unknown path.
E.g. ``["com.example.payments", "payments/"]``.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from responseiq.schemas.proof import ContextResolutionFailure, ContextResolutionReason

if TYPE_CHECKING:
    from responseiq.config.settings import RepoEntry

logger = logging.getLogger(__name__)

_CACHE_ROOT = Path.home() / ".cache" / "responseiq" / "repos"


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class ResolutionResult:
    """
    Outcome of a single path-resolution attempt.

    Exactly one of ``resolved_path`` or ``failure`` will be set.
    """

    path_str: str
    line_num: int
    resolved_path: Optional[Path] = None
    repo_name: Optional[str] = None  # Which RepoEntry was used
    failure: Optional[ContextResolutionFailure] = None

    @property
    def ok(self) -> bool:
        return self.resolved_path is not None and self.resolved_path.is_file()


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------


class MultiRepoResolver:
    """
    Resolves stack-trace path strings to local ``Path`` objects using a
    ``repo_map`` loaded from ``Settings``.

    Parameters
    ----------
    repo_map:
        ``Dict[str, RepoEntry]`` — typically ``settings.repo_map``.
    """

    def __init__(self, repo_map: Dict[str, "RepoEntry"]) -> None:
        self._repo_map = repo_map

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def resolve(self, path_str: str, line_num: int) -> ResolutionResult:
        """
        Attempt to resolve *path_str* to a local file.

        Returns a ``ResolutionResult`` — never raises.
        """
        attempted: List[str] = []

        # Step 1: find the best-matching RepoEntry
        name, entry = self._match_entry(path_str)
        if entry is None:
            return ResolutionResult(
                path_str=path_str,
                line_num=line_num,
                failure=ContextResolutionFailure(
                    path=path_str,
                    line_num=line_num,
                    reason=ContextResolutionReason.REPO_NOT_CONFIGURED,
                    attempted_repos=[],
                    detail="No matching entry in repo_map for this path.",
                    timestamp=datetime.now(timezone.utc),
                ),
            )

        attempted.append(name)
        effective_path = self._strip_prefix(path_str, entry.path_prefix)

        # Step 2: try local paths
        if entry.local_path is not None:
            local_result = self._try_local(effective_path, entry.local_path, name, line_num)
            if local_result.ok:
                return local_result

        # Step 3: try cache of sparse checkout
        cached = _CACHE_ROOT / name
        if cached.exists():
            cache_result = self._try_local(effective_path, cached, name, line_num)
            if cache_result.ok:
                return cache_result

        # Step 4: sparse checkout from remote
        if entry.remote_url:
            try:
                await self._sparse_checkout(entry.remote_url, entry.git_ref, name)
                cache_result = self._try_local(effective_path, _CACHE_ROOT / name, name, line_num)
                if cache_result.ok:
                    return cache_result
            except Exception as exc:  # noqa: BLE001
                logger.warning("Sparse checkout failed for %s: %s", name, exc)
                return ResolutionResult(
                    path_str=path_str,
                    line_num=line_num,
                    failure=ContextResolutionFailure(
                        path=path_str,
                        line_num=line_num,
                        reason=ContextResolutionReason.REMOTE_CLONE_FAILED,
                        attempted_repos=attempted,
                        detail=str(exc),
                        timestamp=datetime.now(timezone.utc),
                    ),
                )

        return ResolutionResult(
            path_str=path_str,
            line_num=line_num,
            failure=ContextResolutionFailure(
                path=path_str,
                line_num=line_num,
                reason=ContextResolutionReason.FILE_NOT_FOUND,
                attempted_repos=attempted,
                detail=f"File not found under any configured path for repo '{name}'.",
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def resolve_many(self, refs: List[Tuple[str, int]]) -> List[ResolutionResult]:
        """Resolve multiple (path, line_num) pairs concurrently."""
        tasks = [self.resolve(path_str, line_num) for path_str, line_num in refs]
        return list(await asyncio.gather(*tasks))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _match_entry(self, path_str: str) -> Tuple[str, Optional["RepoEntry"]]:
        """
        Return the first ``(name, RepoEntry)`` whose ``service_prefixes`` or
        ``path_prefix`` matches *path_str*.

        Falls back to the entry named ``"default"`` if present.
        """
        for name, entry in self._repo_map.items():
            # 1. Explicit service prefix match
            for prefix in entry.service_prefixes:
                if path_str.startswith(prefix) or (f"/{prefix}" in path_str) or (f"/{prefix}/" in f"/{path_str}"):
                    return name, entry
            # 2. Path-prefix match (monorepo)
            if entry.path_prefix and path_str.startswith(entry.path_prefix):
                return name, entry

        # 3. Default catch-all
        default = self._repo_map.get("default")
        if default is not None:
            return "default", default

        return "", None

    @staticmethod
    def _strip_prefix(path_str: str, prefix: str) -> str:
        """Remove *prefix* from the start of *path_str* (normalize slashes)."""
        if not prefix:
            return path_str
        prefix_norm = prefix.rstrip("/") + "/"
        path_norm = path_str.lstrip("/")
        if path_norm.startswith(prefix_norm.lstrip("/")):
            return path_norm[len(prefix_norm.lstrip("/")) :]
        return path_str

    @staticmethod
    def _try_local(effective_path: str, base: Path, repo_name: str, line_num: int) -> ResolutionResult:
        """Try to find *effective_path* under *base* using the same suffix-walk
        as ``resolve_local_path`` in context_extractor."""
        p = Path(effective_path)

        # Direct hit
        candidate = base / p
        if candidate.exists() and candidate.is_file():
            return ResolutionResult(
                path_str=effective_path,
                line_num=line_num,
                resolved_path=candidate,
                repo_name=repo_name,
            )

        # Suffix walk: strip leading parts one at a time
        parts = p.parts
        for i in range(1, len(parts)):
            sub = Path(*parts[i:])
            candidate = base / sub
            if candidate.exists() and candidate.is_file():
                return ResolutionResult(
                    path_str=effective_path,
                    line_num=line_num,
                    resolved_path=candidate,
                    repo_name=repo_name,
                )

        # Not found — return a non-ok result (failure=None marks "tried but missed")
        return ResolutionResult(path_str=effective_path, line_num=line_num)

    @staticmethod
    async def _sparse_checkout(remote_url: str, git_ref: str, name: str) -> None:
        """
        Perform a depth-1 clone (or fetch) of *remote_url* at *git_ref* into
        ``~/.cache/responseiq/repos/<name>/``.

        Uses ``--filter=blob:none`` for a blobless clone so we get the full
        tree without every blob, then ``git checkout`` to materialise only what
        we need.
        """
        dest = _CACHE_ROOT / name
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists():
            # Repo already cloned — just fetch the latest ref
            logger.debug("Fetching %s from %s at %s", name, remote_url, git_ref)
            proc = await asyncio.create_subprocess_exec(
                "git",
                "-C",
                str(dest),
                "fetch",
                "--depth=1",
                "origin",
                git_ref,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"git fetch failed: {stderr.decode().strip()}")
            # Reset to fetched ref
            proc2 = await asyncio.create_subprocess_exec(
                "git",
                "-C",
                str(dest),
                "checkout",
                "FETCH_HEAD",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr2 = await proc2.communicate()
            if proc2.returncode != 0:
                raise RuntimeError(f"git checkout FETCH_HEAD failed: {stderr2.decode().strip()}")
        else:
            logger.debug("Cloning %s from %s at %s", name, remote_url, git_ref)
            proc = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                "--filter=blob:none",
                "--depth=1",
                "--branch",
                git_ref,
                remote_url,
                str(dest),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                # branch form failed — try with commit SHA via init+fetch
                dest.mkdir(parents=True, exist_ok=True)
                for cmd in [
                    ["git", "-C", str(dest), "init"],
                    ["git", "-C", str(dest), "remote", "add", "origin", remote_url],
                    ["git", "-C", str(dest), "fetch", "--depth=1", "origin", git_ref],
                    ["git", "-C", str(dest), "checkout", "FETCH_HEAD"],
                ]:
                    p2 = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    _, e2 = await p2.communicate()
                    if p2.returncode != 0:
                        raise RuntimeError(f"git init/fetch fallback failed at {cmd}: {e2.decode().strip()}")
