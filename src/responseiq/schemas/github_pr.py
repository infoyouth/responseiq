"""src/responseiq/schemas/github_pr.py

P8: Headless PR Interventions — GitHub App webhook event schemas.

Supported GitHub webhook event types
─────────────────────────────────────
  issue_comment   — engineer types a /responseiq command on a PR comment
  pull_request    — bot detects a ResponseIQ-authored PR (opened / reopened)

Command grammar
───────────────
    /responseiq approve           Confirm and merge the suggested fix PR.
    /responseiq rollback          Revert last applied remediation on this PR.
    /responseiq status            Post a ProofBundle summary as a PR comment.
    /responseiq explain           Post full rationale + blast_radius as comment.
    /responseiq help              List available commands.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── enums ─────────────────────────────────────────────────────────────────────


class GitHubEventType(str, Enum):
    ISSUE_COMMENT = "issue_comment"
    PULL_REQUEST = "pull_request"
    PING = "ping"
    UNKNOWN = "unknown"


class PRBotCommand(str, Enum):
    APPROVE = "approve"
    ROLLBACK = "rollback"
    STATUS = "status"
    EXPLAIN = "explain"
    HELP = "help"
    UNKNOWN = "unknown"


# ── nested models ─────────────────────────────────────────────────────────────


class GitHubUser(BaseModel):
    login: str
    id: int
    type: str = "User"


class GitHubRepo(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool = False


class GitHubIssue(BaseModel):
    number: int
    title: str
    state: str = "open"
    pull_request: Optional[Dict[str, Any]] = None

    @property
    def is_pull_request(self) -> bool:
        return self.pull_request is not None


class GitHubComment(BaseModel):
    id: int
    body: str
    user: GitHubUser
    html_url: str = ""


class GitHubPullRequest(BaseModel):
    number: int
    title: str
    state: str = "open"
    head: Dict[str, Any] = Field(default_factory=dict)
    base: Dict[str, Any] = Field(default_factory=dict)
    labels: List[Dict[str, Any]] = Field(default_factory=list)
    html_url: str = ""

    @property
    def label_names(self) -> List[str]:
        return [lbl.get("name", "") for lbl in self.labels]

    @property
    def is_responseiq_pr(self) -> bool:
        """True if the PR was created by the ResponseIQ bot."""
        return any(label in self.label_names for label in ("responseiq", "responseiq-fix", "automated-fix"))


class GitHubInstallation(BaseModel):
    id: int


# ── event payloads ────────────────────────────────────────────────────────────


class IssueCommentPayload(BaseModel):
    """GitHub `issue_comment` webhook payload (PR comments)."""

    action: str  # "created" | "edited" | "deleted"
    issue: GitHubIssue
    comment: GitHubComment
    repository: GitHubRepo
    sender: GitHubUser
    installation: Optional[GitHubInstallation] = None


class PullRequestPayload(BaseModel):
    """GitHub `pull_request` webhook payload."""

    action: str  # "opened" | "reopened" | "closed" | "labeled" | ...
    pull_request: GitHubPullRequest
    repository: GitHubRepo
    sender: GitHubUser
    installation: Optional[GitHubInstallation] = None


# ── parsed command ────────────────────────────────────────────────────────────


class ParsedBotCommand(BaseModel):
    """Result of parsing a /responseiq comment."""

    raw_body: str
    command: PRBotCommand
    args: List[str] = Field(default_factory=list)
    pr_number: int
    repo_full_name: str
    actor: str  # GitHub login of the commenter
    comment_id: int

    @property
    def is_valid(self) -> bool:
        return self.command != PRBotCommand.UNKNOWN


# ── response ──────────────────────────────────────────────────────────────────


class GitHubWebhookAck(BaseModel):
    """Standard acknowledgement returned to GitHub."""

    status: str = "accepted"
    event: str = "unknown"
    command: Optional[str] = None
    pr_number: Optional[int] = None
    message: str = ""
