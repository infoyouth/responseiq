# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Prepare and validate remediation branches in isolated git worktrees."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from responseiq.utils.git_utils import GitClient
from responseiq.utils.logger import logger


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


class WorktreePreparationError(RuntimeError):
    """Raised when a remediation cannot be prepared and validated safely."""


class WorktreeValidationError(WorktreePreparationError):
    """Raised when the candidate patch cannot apply or a validation command fails."""


@dataclass(frozen=True)
class PreparedBranch:
    """Remote branch created from a validated isolated worktree."""

    branch_name: str
    commit_sha: str
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut: MutantDict = {}  # type: ignore
mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut: MutantDict = {}  # type: ignore
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut: MutantDict = {}  # type: ignore
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut: MutantDict = {}  # type: ignore
mutants_xǁWorktreePreparationServiceǁ_run__mutmut: MutantDict = {}  # type: ignore
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut: MutantDict = {}  # type: ignore


class WorktreePreparationService:
    """Apply an explicit patch, validate it, and publish the resulting branch."""

    @_mutmut_mutated(mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut)
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_orig(
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_1(
        self,
        *,
        repo_path: Path,
        repo_name: str,
        patch_text: str,
        validation_commands: Sequence[Sequence[str]],
        required_checks: Sequence[str] = (),
        token: str,
        base: str = "XXmainXX",
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_2(
        self,
        *,
        repo_path: Path,
        repo_name: str,
        patch_text: str,
        validation_commands: Sequence[Sequence[str]],
        required_checks: Sequence[str] = (),
        token: str,
        base: str = "MAIN",
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_3(
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
        if patch_text.strip():
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_4(
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
            raise WorktreePreparationError(None)
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_5(
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
            raise WorktreePreparationError("XXA non-empty unified diff is requiredXX")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_6(
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
            raise WorktreePreparationError("a non-empty unified diff is required")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_7(
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
            raise WorktreePreparationError("A NON-EMPTY UNIFIED DIFF IS REQUIRED")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_8(
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
        if not validation_commands or not required_checks:
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_9(
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
        if validation_commands and not required_checks:
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_10(
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
        if not validation_commands and required_checks:
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_11(
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
            raise WorktreePreparationError(None)
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_12(
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
            raise WorktreePreparationError("XXAt least one validation command is requiredXX")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_13(
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
            raise WorktreePreparationError("at least one validation command is required")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_14(
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
            raise WorktreePreparationError("AT LEAST ONE VALIDATION COMMAND IS REQUIRED")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_15(
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
        if token:
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_16(
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
            raise WorktreePreparationError(None)

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_17(
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
            raise WorktreePreparationError("XXA GitHub token is required to push the validated branchXX")

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_18(
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
            raise WorktreePreparationError("a github token is required to push the validated branch")

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_19(
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
            raise WorktreePreparationError("A GITHUB TOKEN IS REQUIRED TO PUSH THE VALIDATED BRANCH")

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_20(
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

        branch = None
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_21(
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

        branch = branch_name and f"responseiq-fix-{uuid.uuid4().hex[:12]}"
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_22(
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

        branch = branch_name or f"responseiq-fix-{uuid.uuid4().hex[:13]}"
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_23(
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
        worktree_path = None
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_24(
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
        worktree_path = Path(None)
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_25(
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
        worktree_path = Path(tempfile.mkdtemp(prefix=None, dir=repo_path.parent))
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_26(
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
        worktree_path = Path(tempfile.mkdtemp(prefix="responseiq-worktree-", dir=None))
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_27(
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
        worktree_path = Path(tempfile.mkdtemp(dir=repo_path.parent))
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_28(
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
        worktree_path = Path(tempfile.mkdtemp(prefix="responseiq-worktree-", ))
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_29(
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
        worktree_path = Path(tempfile.mkdtemp(prefix="XXresponseiq-worktree-XX", dir=repo_path.parent))
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_30(
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
        worktree_path = Path(tempfile.mkdtemp(prefix="RESPONSEIQ-WORKTREE-", dir=repo_path.parent))
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_31(
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
        patch_path = None

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_32(
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
        patch_path = worktree_path.parent * f"{worktree_path.name}.patch"

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_33(
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
            self._run_git(None, ["worktree", "add", "-b", branch, str(worktree_path), base])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_34(
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
            self._run_git(repo_path, None)
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_35(
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
            self._run_git(["worktree", "add", "-b", branch, str(worktree_path), base])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_36(
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
            self._run_git(repo_path, )
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_37(
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
            self._run_git(repo_path, ["XXworktreeXX", "add", "-b", branch, str(worktree_path), base])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_38(
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
            self._run_git(repo_path, ["WORKTREE", "add", "-b", branch, str(worktree_path), base])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_39(
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
            self._run_git(repo_path, ["worktree", "XXaddXX", "-b", branch, str(worktree_path), base])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_40(
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
            self._run_git(repo_path, ["worktree", "ADD", "-b", branch, str(worktree_path), base])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_41(
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
            self._run_git(repo_path, ["worktree", "add", "XX-bXX", branch, str(worktree_path), base])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_42(
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
            self._run_git(repo_path, ["worktree", "add", "-B", branch, str(worktree_path), base])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_43(
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
            self._run_git(repo_path, ["worktree", "add", "-b", branch, str(None), base])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_44(
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
            patch_path.write_text(None, encoding="utf-8")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_45(
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
            patch_path.write_text(patch_text, encoding=None)
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_46(
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
            patch_path.write_text(encoding="utf-8")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_47(
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
            patch_path.write_text(patch_text, )
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_48(
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
            patch_path.write_text(patch_text, encoding="XXutf-8XX")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_49(
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
            patch_path.write_text(patch_text, encoding="UTF-8")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_50(
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
                self._run_git(None, ["apply", "--check", str(patch_path)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_51(
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
                self._run_git(worktree_path, None)
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_52(
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
                self._run_git(["apply", "--check", str(patch_path)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_53(
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
                self._run_git(worktree_path, )
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_54(
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
                self._run_git(worktree_path, ["XXapplyXX", "--check", str(patch_path)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_55(
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
                self._run_git(worktree_path, ["APPLY", "--check", str(patch_path)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_56(
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
                self._run_git(worktree_path, ["apply", "XX--checkXX", str(patch_path)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_57(
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
                self._run_git(worktree_path, ["apply", "--CHECK", str(patch_path)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_58(
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
                self._run_git(worktree_path, ["apply", "--check", str(None)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_59(
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
                self._run_git(None, ["apply", str(patch_path)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_60(
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
                self._run_git(worktree_path, None)
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_61(
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
                self._run_git(["apply", str(patch_path)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_62(
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
                self._run_git(worktree_path, )
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_63(
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
                self._run_git(worktree_path, ["XXapplyXX", str(patch_path)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_64(
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
                self._run_git(worktree_path, ["APPLY", str(patch_path)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_65(
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
                self._run_git(worktree_path, ["apply", str(None)])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_66(
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
                if not command and any(not part for part in command):
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_67(
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
                if command or any(not part for part in command):
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_68(
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
                if not command or any(None):
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_69(
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
                if not command or any(part for part in command):
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_70(
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
                    raise WorktreeValidationError(None)
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_71(
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
                    raise WorktreeValidationError("XXValidation commands must contain non-empty argv entriesXX")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_72(
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
                    raise WorktreeValidationError("validation commands must contain non-empty argv entries")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_73(
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
                    raise WorktreeValidationError("VALIDATION COMMANDS MUST CONTAIN NON-EMPTY ARGV ENTRIES")
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_74(
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
                self._run_command(None, command)

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_75(
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
                self._run_command(worktree_path, None)

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_76(
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
                self._run_command(command)

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_77(
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
                self._run_command(worktree_path, )

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_78(
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

            self._run_required_checks(None, required_checks, validation_commands)

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_79(
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

            self._run_required_checks(worktree_path, None, validation_commands)

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_80(
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

            self._run_required_checks(worktree_path, required_checks, None)

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_81(
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

            self._run_required_checks(required_checks, validation_commands)

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_82(
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

            self._run_required_checks(worktree_path, validation_commands)

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_83(
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

            self._run_required_checks(worktree_path, required_checks, )

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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_84(
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

            self._run_git(None, ["config", "user.name", "ResponseIQ Bot"])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_85(
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

            self._run_git(worktree_path, None)
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_86(
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

            self._run_git(["config", "user.name", "ResponseIQ Bot"])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_87(
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

            self._run_git(worktree_path, )
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_88(
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

            self._run_git(worktree_path, ["XXconfigXX", "user.name", "ResponseIQ Bot"])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_89(
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

            self._run_git(worktree_path, ["CONFIG", "user.name", "ResponseIQ Bot"])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_90(
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

            self._run_git(worktree_path, ["config", "XXuser.nameXX", "ResponseIQ Bot"])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_91(
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

            self._run_git(worktree_path, ["config", "USER.NAME", "ResponseIQ Bot"])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_92(
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

            self._run_git(worktree_path, ["config", "user.name", "XXResponseIQ BotXX"])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_93(
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

            self._run_git(worktree_path, ["config", "user.name", "responseiq bot"])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_94(
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

            self._run_git(worktree_path, ["config", "user.name", "RESPONSEIQ BOT"])
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

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_95(
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
            self._run_git(None, ["config", "user.email", "bot@responseiq.io"])
            self._run_git(worktree_path, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_96(
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
            self._run_git(worktree_path, None)
            self._run_git(worktree_path, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_97(
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
            self._run_git(["config", "user.email", "bot@responseiq.io"])
            self._run_git(worktree_path, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_98(
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
            self._run_git(worktree_path, )
            self._run_git(worktree_path, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_99(
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
            self._run_git(worktree_path, ["XXconfigXX", "user.email", "bot@responseiq.io"])
            self._run_git(worktree_path, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_100(
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
            self._run_git(worktree_path, ["CONFIG", "user.email", "bot@responseiq.io"])
            self._run_git(worktree_path, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_101(
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
            self._run_git(worktree_path, ["config", "XXuser.emailXX", "bot@responseiq.io"])
            self._run_git(worktree_path, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_102(
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
            self._run_git(worktree_path, ["config", "USER.EMAIL", "bot@responseiq.io"])
            self._run_git(worktree_path, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_103(
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
            self._run_git(worktree_path, ["config", "user.email", "XXbot@responseiq.ioXX"])
            self._run_git(worktree_path, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_104(
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
            self._run_git(worktree_path, ["config", "user.email", "BOT@RESPONSEIQ.IO"])
            self._run_git(worktree_path, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_105(
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
            self._run_git(None, ["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_106(
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
            self._run_git(worktree_path, None)
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_107(
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
            self._run_git(["add", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_108(
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
            self._run_git(worktree_path, )
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_109(
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
            self._run_git(worktree_path, ["XXaddXX", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_110(
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
            self._run_git(worktree_path, ["ADD", "--all"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_111(
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
            self._run_git(worktree_path, ["add", "XX--allXX"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_112(
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
            self._run_git(worktree_path, ["add", "--ALL"])
            self._run_git(worktree_path, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_113(
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
            self._run_git(None, ["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_114(
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
            self._run_git(worktree_path, None)
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_115(
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
            self._run_git(["commit", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_116(
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
            self._run_git(worktree_path, )
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_117(
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
            self._run_git(worktree_path, ["XXcommitXX", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_118(
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
            self._run_git(worktree_path, ["COMMIT", "-m", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_119(
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
            self._run_git(worktree_path, ["commit", "XX-mXX", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_120(
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
            self._run_git(worktree_path, ["commit", "-M", "fix: validated ResponseIQ remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_121(
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
            self._run_git(worktree_path, ["commit", "-m", "XXfix: validated ResponseIQ remediationXX"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_122(
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
            self._run_git(worktree_path, ["commit", "-m", "fix: validated responseiq remediation"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_123(
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
            self._run_git(worktree_path, ["commit", "-m", "FIX: VALIDATED RESPONSEIQ REMEDIATION"])
            commit_sha = self._run_git(worktree_path, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_124(
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
            commit_sha = None

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_125(
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
            commit_sha = self._run_git(None, ["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_126(
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
            commit_sha = self._run_git(worktree_path, None).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_127(
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
            commit_sha = self._run_git(["rev-parse", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_128(
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
            commit_sha = self._run_git(worktree_path, ).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_129(
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
            commit_sha = self._run_git(worktree_path, ["XXrev-parseXX", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_130(
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
            commit_sha = self._run_git(worktree_path, ["REV-PARSE", "HEAD"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_131(
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
            commit_sha = self._run_git(worktree_path, ["rev-parse", "XXHEADXX"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_132(
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
            commit_sha = self._run_git(worktree_path, ["rev-parse", "head"]).strip()

            if not GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_133(
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

            if GitClient(cwd=worktree_path).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_134(
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

            if not GitClient(cwd=worktree_path).push(None, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_135(
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

            if not GitClient(cwd=worktree_path).push(branch, None, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_136(
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

            if not GitClient(cwd=worktree_path).push(branch, token, None):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_137(
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

            if not GitClient(cwd=worktree_path).push(token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_138(
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

            if not GitClient(cwd=worktree_path).push(branch, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_139(
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

            if not GitClient(cwd=worktree_path).push(branch, token, ):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_140(
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

            if not GitClient(cwd=None).push(branch, token, repo_name):
                raise WorktreePreparationError("Failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_141(
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
                raise WorktreePreparationError(None)

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_142(
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
                raise WorktreePreparationError("XXFailed to push the validated remediation branchXX")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_143(
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
                raise WorktreePreparationError("failed to push the validated remediation branch")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_144(
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
                raise WorktreePreparationError("FAILED TO PUSH THE VALIDATED REMEDIATION BRANCH")

            return PreparedBranch(branch_name=branch, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_145(
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

            return PreparedBranch(branch_name=None, commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_146(
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

            return PreparedBranch(branch_name=branch, commit_sha=None)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_147(
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

            return PreparedBranch(commit_sha=commit_sha)
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_148(
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

            return PreparedBranch(branch_name=branch, )
        finally:
            patch_path.unlink(missing_ok=True)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_149(
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
            patch_path.unlink(missing_ok=None)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_150(
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
            patch_path.unlink(missing_ok=False)
            self._remove_worktree(repo_path, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_151(
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
            self._remove_worktree(None, worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_152(
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
            self._remove_worktree(repo_path, None)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_153(
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
            self._remove_worktree(worktree_path)

    def xǁWorktreePreparationServiceǁprepare_and_push__mutmut_154(
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
            self._remove_worktree(repo_path, )

    @staticmethod
    @_mutmut_mutated(mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut)
    def _run_git(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(["git", *args], cwd, "git")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_git__mutmut_orig(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(["git", *args], cwd, "git")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_git__mutmut_1(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(None, cwd, "git")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_git__mutmut_2(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(["git", *args], None, "git")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_git__mutmut_3(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(["git", *args], cwd, None)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_git__mutmut_4(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(cwd, "git")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_git__mutmut_5(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(["git", *args], "git")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_git__mutmut_6(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(["git", *args], cwd, )

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_git__mutmut_7(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(["XXgitXX", *args], cwd, "git")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_git__mutmut_8(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(["GIT", *args], cwd, "git")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_git__mutmut_9(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(["git", *args], cwd, "XXgitXX")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_git__mutmut_10(cwd: Path, args: list[str]) -> str:
        return WorktreePreparationService._run(["git", *args], cwd, "GIT")

    @staticmethod
    @_mutmut_mutated(mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut)
    def _run_command(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(list(command), cwd, "validation")
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_orig(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(list(command), cwd, "validation")
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_1(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(None, cwd, "validation")
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_2(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(list(command), None, "validation")
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_3(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(list(command), cwd, None)
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_4(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(cwd, "validation")
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_5(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(list(command), "validation")
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_6(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(list(command), cwd, )
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_7(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(list(None), cwd, "validation")
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_8(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(list(command), cwd, "XXvalidationXX")
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_9(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(list(command), cwd, "VALIDATION")
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(exc)) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_10(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(list(command), cwd, "validation")
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(None) from exc

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_command__mutmut_11(cwd: Path, command: Sequence[str]) -> str:
        try:
            return WorktreePreparationService._run(list(command), cwd, "validation")
        except WorktreePreparationError as exc:
            raise WorktreeValidationError(str(None)) from exc

    @staticmethod
    @_mutmut_mutated(mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut)
    def _run_required_checks(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_orig(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_1(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = None
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_2(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(None)
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_3(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(None, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_4(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, None).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_5(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_6(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_7(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["XXdiffXX", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_8(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["DIFF", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_9(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "XX--name-onlyXX"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_10(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--NAME-ONLY"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_11(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = None
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_12(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            None,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_13(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            None,
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_14(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_15(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_16(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["XXls-filesXX", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_17(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["LS-FILES", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_18(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "XX--othersXX", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_19(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--OTHERS", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_20(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "XX--exclude-standardXX"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_21(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--EXCLUDE-STANDARD"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_22(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = None

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_23(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(None)

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_24(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(None) if path.endswith(".py"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_25(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(None))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_26(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith("XX.pyXX"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_27(
        cwd: Path,
        required_checks: Sequence[str],
        validation_commands: Sequence[Sequence[str]],
    ) -> None:
        changed_files = set(WorktreePreparationService._run_git(cwd, ["diff", "--name-only"]).splitlines())
        untracked_files = WorktreePreparationService._run_git(
            cwd,
            ["ls-files", "--others", "--exclude-standard"],
        ).splitlines()
        python_files = sorted(path for path in changed_files.union(untracked_files) if path.endswith(".PY"))

        for check_name in required_checks:
            if check_name == "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_28(
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
            if check_name != "tests":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_29(
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
            if check_name == "XXtestsXX":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_30(
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
            if check_name == "TESTS":
                if not any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_31(
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
                if any("pytest" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_32(
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
                if not any(None):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_33(
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
                if not any("XXpytestXX" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_34(
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
                if not any("PYTEST" in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_35(
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
                if not any("pytest" not in part for command in validation_commands for part in command):
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_36(
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
                    WorktreePreparationService._run_command(None, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_37(
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
                    WorktreePreparationService._run_command(cwd, None)
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_38(
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
                    WorktreePreparationService._run_command([sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_39(
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
                    WorktreePreparationService._run_command(cwd, )
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_40(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "XX-mXX", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_41(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-M", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_42(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "XXpytestXX", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_43(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "PYTEST", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_44(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "XX-qXX"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_45(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-Q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_46(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name != "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_47(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "XXsecurity_scanXX":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_48(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "SECURITY_SCAN":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_49(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        None,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_50(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        None,
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_51(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_52(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_53(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["XXruffXX", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_54(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["RUFF", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_55(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "XXcheckXX", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_56(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "CHECK", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_57(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "XX--selectXX", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_58(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--SELECT", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_59(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "XXSXX", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_60(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "s", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_61(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name != "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_62(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "XXsyntax_checkXX":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_63(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "SYNTAX_CHECK":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_64(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        None,
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_65(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        None,
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_66(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        [sys.executable, "-m", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_67(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_68(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "XX-mXX", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_69(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-M", "py_compile", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_70(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "XXpy_compileXX", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_71(
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
                    WorktreePreparationService._run_command(cwd, [sys.executable, "-m", "pytest", "-q"])
            elif check_name == "security_scan":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        ["ruff", "check", "--select", "S", *python_files],
                    )
            elif check_name == "syntax_check":
                if python_files:
                    WorktreePreparationService._run_command(
                        cwd,
                        [sys.executable, "-m", "PY_COMPILE", *python_files],
                    )
            else:
                raise WorktreeValidationError(f"Unknown required candidate check: {check_name}")

    @staticmethod
    @_mutmut_mutated(mutants_xǁWorktreePreparationServiceǁ_run__mutmut)
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
    def xǁWorktreePreparationServiceǁ_run__mutmut_orig(command: list[str], cwd: Path, kind: str) -> str:
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
    def xǁWorktreePreparationServiceǁ_run__mutmut_1(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = None
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_2(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                None,
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
    def xǁWorktreePreparationServiceǁ_run__mutmut_3(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=None,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_4(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=None,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_5(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=None,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_6(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=None,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_7(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
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
    def xǁWorktreePreparationServiceǁ_run__mutmut_8(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_9(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_10(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_11(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_12(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=False,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_13(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=False,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_14(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_15(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = None
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_16(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) and str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_17(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(None, "stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_18(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, None, None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_19(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr("stderr", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_20(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_21(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", ) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_22(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "XXstderrXX", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_23(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "STDERR", None) or str(exc)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_24(command: list[str], cwd: Path, kind: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = getattr(exc, "stderr", None) or str(None)
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_25(command: list[str], cwd: Path, kind: str) -> str:
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
            raise WorktreePreparationError(None) from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_26(command: list[str], cwd: Path, kind: str) -> str:
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
            raise WorktreePreparationError(f"{kind} command failed: {' '.join(None)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    def xǁWorktreePreparationServiceǁ_run__mutmut_27(command: list[str], cwd: Path, kind: str) -> str:
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
            raise WorktreePreparationError(f"{kind} command failed: {'XX XX'.join(command)}: {detail.strip()}") from exc
        return result.stdout

    @staticmethod
    @_mutmut_mutated(mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut)
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

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_orig(repo_path: Path, worktree_path: Path) -> None:
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

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_1(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                None,  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_2(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=None,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_3(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=None,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_4(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=None,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_5(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=None,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_6(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_7(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_8(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_9(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_10(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_11(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["XXgitXX", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_12(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["GIT", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_13(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "XXworktreeXX", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_14(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "WORKTREE", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_15(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "XXremoveXX", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_16(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "REMOVE", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_17(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "XX--forceXX", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_18(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--FORCE", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_19(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(None)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_20(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=False,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_21(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=False,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_22(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_23(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning(None, exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_24(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", None)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_25(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning(exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_26(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("Failed to remove temporary ResponseIQ worktree: %s", )
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_27(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("XXFailed to remove temporary ResponseIQ worktree: %sXX", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_28(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("failed to remove temporary responseiq worktree: %s", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_29(repo_path: Path, worktree_path: Path) -> None:
        try:
            subprocess.run(  # noqa: S603, S607
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.warning("FAILED TO REMOVE TEMPORARY RESPONSEIQ WORKTREE: %S", exc)
        finally:
            shutil.rmtree(worktree_path, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_30(repo_path: Path, worktree_path: Path) -> None:
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
            shutil.rmtree(None, ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_31(repo_path: Path, worktree_path: Path) -> None:
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
            shutil.rmtree(worktree_path, ignore_errors=None)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_32(repo_path: Path, worktree_path: Path) -> None:
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
            shutil.rmtree(ignore_errors=True)

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_33(repo_path: Path, worktree_path: Path) -> None:
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
            shutil.rmtree(worktree_path, )

    @staticmethod
    def xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_34(repo_path: Path, worktree_path: Path) -> None:
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
            shutil.rmtree(worktree_path, ignore_errors=False)

mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['_mutmut_orig'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_orig # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_1'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_1 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_2'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_2 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_3'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_3 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_4'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_4 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_5'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_5 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_6'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_6 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_7'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_7 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_8'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_8 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_9'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_9 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_10'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_10 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_11'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_11 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_12'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_12 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_13'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_13 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_14'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_14 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_15'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_15 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_16'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_16 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_17'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_17 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_18'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_18 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_19'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_19 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_20'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_20 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_21'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_21 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_22'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_22 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_23'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_23 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_24'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_24 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_25'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_25 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_26'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_26 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_27'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_27 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_28'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_28 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_29'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_29 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_30'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_30 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_31'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_31 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_32'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_32 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_33'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_33 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_34'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_34 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_35'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_35 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_36'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_36 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_37'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_37 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_38'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_38 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_39'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_39 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_40'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_40 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_41'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_41 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_42'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_42 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_43'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_43 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_44'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_44 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_45'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_45 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_46'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_46 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_47'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_47 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_48'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_48 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_49'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_49 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_50'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_50 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_51'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_51 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_52'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_52 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_53'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_53 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_54'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_54 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_55'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_55 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_56'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_56 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_57'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_57 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_58'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_58 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_59'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_59 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_60'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_60 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_61'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_61 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_62'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_62 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_63'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_63 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_64'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_64 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_65'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_65 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_66'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_66 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_67'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_67 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_68'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_68 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_69'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_69 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_70'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_70 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_71'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_71 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_72'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_72 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_73'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_73 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_74'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_74 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_75'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_75 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_76'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_76 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_77'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_77 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_78'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_78 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_79'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_79 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_80'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_80 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_81'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_81 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_82'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_82 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_83'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_83 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_84'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_84 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_85'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_85 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_86'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_86 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_87'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_87 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_88'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_88 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_89'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_89 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_90'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_90 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_91'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_91 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_92'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_92 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_93'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_93 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_94'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_94 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_95'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_95 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_96'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_96 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_97'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_97 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_98'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_98 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_99'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_99 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_100'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_100 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_101'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_101 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_102'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_102 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_103'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_103 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_104'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_104 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_105'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_105 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_106'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_106 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_107'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_107 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_108'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_108 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_109'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_109 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_110'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_110 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_111'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_111 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_112'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_112 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_113'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_113 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_114'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_114 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_115'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_115 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_116'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_116 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_117'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_117 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_118'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_118 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_119'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_119 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_120'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_120 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_121'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_121 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_122'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_122 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_123'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_123 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_124'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_124 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_125'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_125 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_126'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_126 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_127'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_127 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_128'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_128 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_129'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_129 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_130'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_130 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_131'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_131 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_132'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_132 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_133'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_133 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_134'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_134 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_135'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_135 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_136'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_136 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_137'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_137 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_138'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_138 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_139'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_139 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_140'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_140 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_141'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_141 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_142'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_142 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_143'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_143 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_144'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_144 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_145'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_145 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_146'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_146 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_147'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_147 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_148'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_148 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_149'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_149 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_150'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_150 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_151'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_151 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_152'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_152 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_153'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_153 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁprepare_and_push__mutmut['xǁWorktreePreparationServiceǁprepare_and_push__mutmut_154'] = WorktreePreparationService.xǁWorktreePreparationServiceǁprepare_and_push__mutmut_154 # type: ignore # mutmut generated

mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut['_mutmut_orig'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_git__mutmut_orig # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut['xǁWorktreePreparationServiceǁ_run_git__mutmut_1'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_git__mutmut_1 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut['xǁWorktreePreparationServiceǁ_run_git__mutmut_2'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_git__mutmut_2 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut['xǁWorktreePreparationServiceǁ_run_git__mutmut_3'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_git__mutmut_3 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut['xǁWorktreePreparationServiceǁ_run_git__mutmut_4'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_git__mutmut_4 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut['xǁWorktreePreparationServiceǁ_run_git__mutmut_5'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_git__mutmut_5 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut['xǁWorktreePreparationServiceǁ_run_git__mutmut_6'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_git__mutmut_6 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut['xǁWorktreePreparationServiceǁ_run_git__mutmut_7'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_git__mutmut_7 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut['xǁWorktreePreparationServiceǁ_run_git__mutmut_8'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_git__mutmut_8 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut['xǁWorktreePreparationServiceǁ_run_git__mutmut_9'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_git__mutmut_9 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_git__mutmut['xǁWorktreePreparationServiceǁ_run_git__mutmut_10'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_git__mutmut_10 # type: ignore # mutmut generated

mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['_mutmut_orig'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_orig # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['xǁWorktreePreparationServiceǁ_run_command__mutmut_1'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_1 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['xǁWorktreePreparationServiceǁ_run_command__mutmut_2'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_2 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['xǁWorktreePreparationServiceǁ_run_command__mutmut_3'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_3 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['xǁWorktreePreparationServiceǁ_run_command__mutmut_4'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_4 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['xǁWorktreePreparationServiceǁ_run_command__mutmut_5'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_5 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['xǁWorktreePreparationServiceǁ_run_command__mutmut_6'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_6 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['xǁWorktreePreparationServiceǁ_run_command__mutmut_7'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_7 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['xǁWorktreePreparationServiceǁ_run_command__mutmut_8'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_8 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['xǁWorktreePreparationServiceǁ_run_command__mutmut_9'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_9 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['xǁWorktreePreparationServiceǁ_run_command__mutmut_10'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_10 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_command__mutmut['xǁWorktreePreparationServiceǁ_run_command__mutmut_11'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_command__mutmut_11 # type: ignore # mutmut generated

mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['_mutmut_orig'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_orig # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_1'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_1 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_2'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_2 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_3'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_3 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_4'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_4 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_5'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_5 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_6'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_6 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_7'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_7 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_8'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_8 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_9'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_9 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_10'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_10 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_11'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_11 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_12'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_12 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_13'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_13 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_14'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_14 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_15'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_15 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_16'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_16 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_17'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_17 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_18'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_18 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_19'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_19 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_20'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_20 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_21'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_21 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_22'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_22 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_23'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_23 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_24'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_24 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_25'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_25 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_26'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_26 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_27'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_27 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_28'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_28 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_29'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_29 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_30'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_30 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_31'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_31 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_32'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_32 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_33'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_33 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_34'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_34 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_35'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_35 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_36'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_36 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_37'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_37 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_38'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_38 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_39'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_39 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_40'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_40 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_41'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_41 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_42'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_42 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_43'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_43 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_44'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_44 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_45'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_45 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_46'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_46 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_47'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_47 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_48'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_48 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_49'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_49 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_50'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_50 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_51'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_51 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_52'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_52 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_53'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_53 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_54'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_54 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_55'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_55 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_56'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_56 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_57'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_57 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_58'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_58 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_59'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_59 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_60'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_60 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_61'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_61 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_62'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_62 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_63'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_63 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_64'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_64 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_65'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_65 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_66'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_66 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_67'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_67 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_68'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_68 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_69'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_69 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_70'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_70 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run_required_checks__mutmut['xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_71'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run_required_checks__mutmut_71 # type: ignore # mutmut generated

mutants_xǁWorktreePreparationServiceǁ_run__mutmut['_mutmut_orig'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_orig # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_1'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_1 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_2'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_2 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_3'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_3 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_4'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_4 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_5'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_5 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_6'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_6 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_7'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_7 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_8'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_8 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_9'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_9 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_10'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_10 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_11'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_11 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_12'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_12 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_13'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_13 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_14'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_14 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_15'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_15 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_16'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_16 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_17'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_17 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_18'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_18 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_19'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_19 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_20'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_20 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_21'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_21 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_22'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_22 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_23'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_23 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_24'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_24 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_25'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_25 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_26'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_26 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_run__mutmut['xǁWorktreePreparationServiceǁ_run__mutmut_27'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_run__mutmut_27 # type: ignore # mutmut generated

mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['_mutmut_orig'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_orig # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_1'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_1 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_2'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_2 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_3'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_3 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_4'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_4 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_5'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_5 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_6'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_6 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_7'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_7 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_8'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_8 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_9'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_9 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_10'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_10 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_11'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_11 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_12'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_12 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_13'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_13 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_14'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_14 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_15'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_15 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_16'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_16 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_17'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_17 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_18'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_18 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_19'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_19 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_20'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_20 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_21'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_21 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_22'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_22 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_23'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_23 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_24'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_24 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_25'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_25 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_26'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_26 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_27'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_27 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_28'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_28 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_29'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_29 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_30'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_30 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_31'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_31 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_32'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_32 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_33'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_33 # type: ignore # mutmut generated
mutants_xǁWorktreePreparationServiceǁ_remove_worktree__mutmut['xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_34'] = WorktreePreparationService.xǁWorktreePreparationServiceǁ_remove_worktree__mutmut_34 # type: ignore # mutmut generated
