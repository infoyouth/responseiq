# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Thin wrapper around Git CLI operations.

``GitClient`` runs ``git`` subprocesses to check out branches, apply
patches, stage files, and create commits. Used by ``GitHubPRService``
to prepare the working tree before opening a pull request.
"""

import os
import subprocess  # nosec B404
from pathlib import Path
from typing import List, Optional

from responseiq.utils.logger import logger


class GitClient:
    def __init__(self, cwd: Optional[Path] = None):
        self.cwd = cwd or Path(os.getcwd())

    def run_with_output(self, args: List[str]) -> Optional[str]:
        """Run a git command and return stdout, or None on failure."""
        try:
            cmd = ["git"] + args
            result = subprocess.run(  # noqa: S603
                cmd,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.debug(f"Git command returned non-zero: {' '.join(cmd)}\nStderr: {e.stderr}")
            return None

    def get_recent_diff(self, since_hours: int = 24, max_commits: int = 10) -> Optional[str]:
        """
        Return a compact unified diff of up to *max_commits* non-merge commits
        made in the last *since_hours* hours.  Output is suitable for LLM consumption.
        """
        return self.run_with_output(
            [
                "log",
                f"--since={since_hours} hours ago",
                "--patch",
                "--unified=2",
                "--no-merges",
                f"--max-count={max_commits}",
                "--format=COMMIT %H %s",
                "--",
            ]
        )

    def get_log_entries(self, since_hours: int = 24, max_commits: int = 20) -> Optional[str]:
        """
        Return one-line log with changed filenames for recent commits.
        Useful for lightweight heuristic symbol matching.
        """
        return self.run_with_output(
            [
                "log",
                f"--since={since_hours} hours ago",
                "--oneline",
                "--no-merges",
                f"--max-count={max_commits}",
                "--name-only",
            ]
        )

    def run(self, args: list) -> bool:
        try:
            cmd = ["git"] + args
            subprocess.run(  # noqa: S603
                cmd,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(cmd)}\nStderr: {e.stderr}")
            return False

    def configure_user(self, name: str = "ResponseIQ Bot", email: str = "bot@responseiq.io"):
        self.run(["config", "user.name", name])
        self.run(["config", "user.email", email])

    def create_branch(self, branch_name: str) -> bool:
        return self.run(["checkout", "-b", branch_name])

    def add_and_commit(self, message: str) -> bool:
        if not self.run(["add", "."]):
            return False
        return self.run(["commit", "-m", message])

    def push(self, branch_name: str, token: str, repo_slug: str) -> bool:
        """
        Pushes changes to remote using the provided token for auth.
        """
        # Formulate auth URL (careful with logging)
        remote_url = f"https://x-access-token:{token}@github.com/{repo_slug}.git"

        # We purposely don't use self.run here to avoid logging the token
        # in case of error in the future
        # (Though our current run implementation logs stderr which might
        # contain it if git echoes it back)
        try:
            subprocess.run(  # noqa: S603
                ["git", "push", remote_url, branch_name],  # noqa: S607
                cwd=self.cwd,
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            # Mask token in error log
            sanitized_msg = e.stderr.replace(token, "***")
            logger.error(f"Git push failed: {sanitized_msg}")
            return False
