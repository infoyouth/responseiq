import os
import subprocess
from pathlib import Path
from typing import Optional

from src.utils.logger import logger


class GitClient:
    def __init__(self, cwd: Optional[Path] = None):
        self.cwd = cwd or Path(os.getcwd())

    def run(self, args: list) -> bool:
        try:
            cmd = ["git"] + args
            subprocess.run(
                cmd, cwd=self.cwd, capture_output=True, text=True, check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(cmd)}\nStderr: {e.stderr}")
            return False

    def configure_user(
        self, name: str = "ResponseIQ Bot", email: str = "bot@responseiq.io"
    ):
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
            subprocess.run(
                ["git", "push", remote_url, branch_name],
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
