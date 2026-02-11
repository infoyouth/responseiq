import os
import time

from src.integrations.github_integration import GitHubIntegration
from src.utils.git_utils import GitClient
from src.utils.logger import logger


class PRService:
    """
    Orchestrates the workflow of:
    1. Creating a git branch
    2. Committing local changes (applied by remediation)
    3. Pushing to remote
    4. Opening a Pull Request via GitHub API
    """

    def __init__(self):
        self.git = GitClient()
        self.gh = GitHubIntegration()

    def create_batch_pr(self, fix_count: int) -> bool:
        """
        Commits all current changes in the workspace and creates a PR.
        Returns True if PR was created successfully.
        """
        repo_name = os.environ.get("GITHUB_REPOSITORY")
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("INPUT_GITHUB_TOKEN")

        if not repo_name:
            logger.warning("Missing GITHUB_REPOSITORY env var. Cannot create PR.")
            return False

        if not token:
            logger.warning("Missing GITHUB_TOKEN env var. Cannot create PR.")
            return False

        # Ensure git is configured
        self.git.configure_user(name="ResponseIQ Bot", email="bot@responseiq.io")

        # Create unique branch
        branch_name = f"responseiq-fix-{int(time.time())}"
        logger.info(f"Preparing to push fixes to branch: {branch_name}")

        if not self.git.create_branch(branch_name):
            logger.error("Failed to create git branch.")
            return False

        # Add and Commit
        commit_msg = f"fix: automated remediation for {fix_count} issues"
        if not self.git.add_and_commit(commit_msg):
            logger.error("Failed to commit changes. Are there any file changes?")
            return False

        # Push to Remote
        if not self.git.push(branch_name, token, repo_name):
            logger.error("Failed to push branch to remote.")
            return False

        # Ensure GH client has token in env for safety if not implicitly set
        if "GITHUB_TOKEN" not in os.environ and token:
            os.environ["GITHUB_TOKEN"] = token
            # Re-init client to pick up token if needed
            self.gh = GitHubIntegration()

        # Create PR
        pr_title = f"fix: ResponseIQ detected {fix_count} issues"
        pr_body = (
            "## 🛡️ ResponseIQ Automated Remediation\n\n"
            f"**ResponseIQ** has detected and fixed **{fix_count}** "
            "critical issues.\n\n"
            "### Changes applied:\n"
            "- Auto-remediated configuration/code based on detected logs.\n\n"
            "Please review the changes before merging."
        )

        pr_url = self.gh.create_pr(repo_name=repo_name, title=pr_title, body=pr_body, head=branch_name)

        if pr_url:
            logger.info(f"🚀 PR Created Successfully: {pr_url}")
            return True
        else:
            logger.error("Failed to create Pull Request via API.")
            return False
