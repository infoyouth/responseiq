# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Prepare and validate remediation branches in isolated git worktrees."""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess  # nosec B404
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from responseiq.services.sandbox_runner import SandboxExecutionError, SandboxLimits, SandboxRunner
from responseiq.utils.git_utils import GitClient
from responseiq.utils.logger import logger


class WorktreePreparationError(RuntimeError):
    """Raised when a remediation cannot be prepared and validated safely."""


class WorktreeValidationError(WorktreePreparationError):
    """Raised when the candidate patch cannot apply or a validation command fails."""


@dataclass(frozen=True)
class PreparedBranch:
    """Remote branch created from a validated isolated worktree."""

    branch_name: str
    commit_sha: str


class WorktreePreparationService:
    """Apply an explicit patch, validate it, and publish the resulting branch."""

    def __init__(self, sandbox_runner: SandboxRunner | None = None) -> None:
        # Keep validation isolated from the caller checkout and strip unapproved env vars.
        # Network namespace isolation is opt-in because some CI and local environments do not
        # expose the required `unshare` capability even though the worktree boundary remains.
        self.sandbox_runner = sandbox_runner or SandboxRunner(SandboxLimits(network_disabled=False))

    def prepare_and_push(
        self,
        *,
        repo_path: Path,
        repo_name: str,
        patch_text: str,
        validation_commands: Sequence[Sequence[str]],
        required_checks: Sequence[str] = (),
        token: str,
        base: str = "main",
        branch_name: str | None = None,
    ) -> PreparedBranch:
        """Prepare a patch outside the caller's checkout and push it after validation."""
        if not patch_text.strip():
            raise WorktreePreparationError("A non-empty unified diff is required")
        if not validation_commands and not required_checks:
            raise WorktreePreparationError("At least one validation command is required")
        if not token:
            raise WorktreePreparationError("A GitHub token is required to push the validated branch")

        branch = branch_name or f"responseiq-fix-{uuid.uuid4().hex[:12]}"
        worktree_path = Path(tempfile.mkdtemp(prefix="responseiq-worktree-", dir=repo_path.parent))
        patch_path = worktree_path.parent / f"{worktree_path.name}.patch"

        try:
            self._run_git(repo_path, ["worktree", "add", "-b", branch, str(worktree_path), base])
            patch_path.write_text(patch_text, encoding="utf-8")
            try:
                self._run_git(worktree_path, ["apply", "--check", str(patch_path)])
                self._run_git(worktree_path, ["apply", str(patch_path)])
            except WorktreePreparationError as exc:
                raise WorktreeValidationError(f"Candidate patch failed to apply: {exc}") from exc

            for command in validation_commands:
                if not command or any(not part for part in command):
                    raise WorktreeValidationError("Validation commands must contain non-empty argv entries")
                self._run_command(worktree_path, command)

            self._run_required_checks(worktree_path, required_checks, validation_commands)

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

    def _run_command(self, cwd: Path, command: Sequence[str]) -> str:
        try:
            safe_env = {
                key: value for key, value in os.environ.items() if key in {"PATH", "PYTHONPATH", "PYTHONNOUSERSITE"}
            }
            result = asyncio.run(self.sandbox_runner.run(list(command), cwd=cwd, environment=safe_env))
            if result.timed_out:
                raise WorktreeValidationError(f"validation command timed out: {' '.join(command)}")
            if result.returncode not in (0, None):
                raise WorktreeValidationError(
                    f"validation command failed ({result.returncode}): {' '.join(command)}\n{result.output.decode('utf-8', errors='replace')}"
                )
            return result.output.decode("utf-8", errors="replace")
        except (SandboxExecutionError, WorktreeValidationError):
            raise
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc
        except Exception as exc:
            raise WorktreeValidationError(f"validation command failed: {' '.join(command)}: {exc}") from exc

    def _run_required_checks(
        self,
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    self._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    self._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    self._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

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
