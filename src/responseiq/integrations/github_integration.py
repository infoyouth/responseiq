# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""GitHub API client wrapper.

Thin layer over ``githubkit`` that handles authentication via
``TokenAuthStrategy``, splits ``owner/repo`` strings, and surfaces
``RequestFailed`` as the single exception type callers need to catch.
Dry-run mode activates automatically when ``RESPONSEIQ_GITHUB_TOKEN`` is unset.
"""

from typing import Optional

from githubkit import GitHub, TokenAuthStrategy
from githubkit.exception import RequestFailed

from responseiq.config.settings import settings
from responseiq.utils.logger import logger


def _split_repo(repo_name: str) -> tuple[str, str]:
    """Split 'owner/repo' into (owner, repo)."""
    parts = repo_name.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid repo name: {repo_name!r}. Expected 'owner/repo'.")
    return parts[0], parts[1]


class GitHubIntegration:
    def __init__(self):
        self.token = settings.github_token.get_secret_value() if settings.github_token else None
        self.client = GitHub(TokenAuthStrategy(self.token)) if self.token else None

    def create_pr(self, repo_name: str, title: str, body: str, head: str, base: str = "main") -> Optional[str]:
        """
        Creates a Pull Request in the specified repository.
        """
        if not self.client:
            logger.warning("GitHub token not configured. Skipping PR creation.")
            return None

        try:
            owner, repo = _split_repo(repo_name)
            response = self.client.rest.pulls.create(
                owner=owner,
                repo=repo,
                title=title,
                body=body,
                head=head,
                base=base,
            )
            html_url = response.parsed_data.html_url
            logger.info(f"Successfully created PR: {html_url}")
            return html_url
        except RequestFailed as e:
            logger.error(f"Failed to create PR in {repo_name}: {e}")
            return None

    def check_permissions(self) -> bool:
        """
        Verifies if the token has valid permissions.
        """
        if not self.client:
            return False
        try:
            response = self.client.rest.users.get_authenticated()
            logger.info(f"Authenticated as GitHub user: {response.parsed_data.login}")
            return True
        except RequestFailed:
            logger.error("GitHub authentication failed.")
            return False
