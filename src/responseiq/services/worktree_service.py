# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Prepare and validate remediation branches in isolated git worktrees."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from responseiq.utils.git_utils import GitClient
from responseiq.utils.logger import logger


class WorktreePreparationError(RuntimeError):
    """Raised when a remediation cannot be prepared and validated safely."""


@dataclass(frozen=True)
class PreparedBranch:
    """Remote branch created from a validated isolated worktree."""

    branch_name: str
    commit_sha: str


class WorktreePreparationService:
    """Apply an explicit patch, validate it, and publish the resulting branch."""

    def prepare_and_push(
        self,
        *,
        repo_path: Path,
        repo_name: str,
        patch_text: str,
        validation_commands: Sequence[Sequence[str]],
        token: str,
        base: str = "main",
        branch_name: str | None = None,
    ) -> PreparedBranch:
        """Prepare a patch outside the caller's checkout and push it after validation."""
        if not patch_text.strip():
            raise WorktreePreparationError("A non-empty unified diff is required")
        if not validation_commands:
            raise WorktreePreparationError("At least one validation command is required")
        if not token:
            raise WorktreePreparationError("A GitHub token is required to push the validated branch")

        branch = branch_name or f"responseiq-fix-{uuid.uuid4().hex[:12]}"
        worktree_path = Path(tempfile.mkdtemp(prefix="responseiq-worktree-", dir=repo_path.parent))
        patch_path = worktree_path.parent / f"{worktree_path.name}.patch"

        try:
            self._run_git(repo_path, ["worktree", "add", "-b", branch, str(worktree_path), base])
            patch_path.write_text(patch_text, encoding="utf-8")
            self._run_git(worktree_path, ["apply", "--check", str(patch_path)])
            self._run_git(worktree_path, ["apply", str(patch_path)])

            for command in validation_commands:
                if not command or any(not part for part in command):
                    raise WorktreePreparationError("Validation commands must contain non-empty argv entries")
                self._run_command(worktree_path, command)

            self._run_git(worktree_path, ["config", "user.name", "ResponseIQ Bot"])
            self._run_git(worktree_path, ["config", "user.email", "bot@responseiq.io"])
            self._run_git(worktree_path, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    @staticmethod
    def _run_git(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(["git", *args], cwd, "git")

    @staticmethod
    def _run_command(cwd: Path, command: Sequence[str]) -> str:
        return WorktreePreparationService._run(list(command), cwd, "validation")

    @staticmethod
    def _run(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def _remove_worktree(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)
