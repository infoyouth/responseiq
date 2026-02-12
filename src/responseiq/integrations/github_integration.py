from typing import Optional

from github import Github, GithubException

from responseiq.config.settings import settings
from responseiq.utils.logger import logger


class GitHubIntegration:
    def __init__(self):
        self.token = settings.github_token.get_secret_value() if settings.github_token else None
        self.client = Github(self.token) if self.token else None

    def create_pr(self, repo_name: str, title: str, body: str, head: str, base: str = "main") -> Optional[str]:
        """
        Creates a Pull Request in the specified repository.
        """
        if not self.client:
            logger.warning("GitHub token not configured. Skipping PR creation.")
            return None

        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.create_pull(title=title, body=body, head=head, base=base)
            logger.info(f"Successfully created PR: {pr.html_url}")
            return pr.html_url
        except GithubException as e:
            logger.error(f"Failed to create PR in {repo_name}: {str(e)}")
            return None

    def check_permissions(self) -> bool:
        """
        Verifies if the token has valid permissions.
        """
        if not self.client:
            return False
        try:
            user = self.client.get_user()
            logger.info(f"Authenticated as GitHub user: {user.login}")
            return True
        except GithubException:
            logger.error("GitHub authentication failed.")
            return False
