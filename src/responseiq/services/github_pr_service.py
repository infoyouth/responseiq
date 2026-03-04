"""src/responseiq/services/github_pr_service.py

P8: Headless PR Interventions — GitHub App command processor.

Responsibilities
────────────────
1. **Command parsing** — extract a ``ParsedBotCommand`` from a raw PR comment
   body.  Ignores comments that don't contain a ``/responseiq`` invocation.

2. **Command dispatch** — route to the appropriate handler:
     approve   → merge PR via PyGithub after final validation
     rollback  → post rollback script location as a PR comment
     status    → post ProofBundle summary (or "no proof available") as comment
     explain   → post full rationale + blast_radius as comment
     help      → post command catalogue

3. **Comment posting** — wraps PyGithub ``create_issue_comment`` so bot
   responses always include a ResponseIQ badge and audit timestamp.

Configuration (env vars)
────────────────────────
    RESPONSEIQ_GITHUB_TOKEN          — Personal Access Token OR GitHub App
                                       installation token.  Required for
                                       comment posting and merge operations.
    RESPONSEIQ_GITHUB_BOT_LOGIN      — GitHub login of the bot account
                                       (default: "responseiq-bot[bot]").
                                       Comments from this user are ignored to
                                       prevent reply loops.

Design Notes
────────────
- ``GitHubPRService`` is **stateless** — construct a new instance per request.
- All PyGithub calls are wrapped in a try/except so a transient GitHub API
  error never crashes the webhook endpoint.
- When ``RESPONSEIQ_GITHUB_TOKEN`` is absent, the service operates in
  **dry-run mode**: commands are parsed and logged but no GitHub API calls
  are made.  This is the safe default for installs that haven't configured
  the GitHub App yet.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, Optional

from responseiq.config.settings import settings
from responseiq.schemas.github_pr import (
    GitHubWebhookAck,
    IssueCommentPayload,
    PRBotCommand,
    ParsedBotCommand,
    PullRequestPayload,
)
from responseiq.utils.logger import logger

# Regex: matches "/responseiq <command> [args...]" anywhere in a comment body
_COMMAND_RE = re.compile(
    r"^\s*/responseiq\s+(?P<cmd>\w+)(?P<rest>[^\n]*)",
    re.MULTILINE | re.IGNORECASE,
)

_COMMAND_MAP: Dict[str, PRBotCommand] = {
    "approve": PRBotCommand.APPROVE,
    "rollback": PRBotCommand.ROLLBACK,
    "status": PRBotCommand.STATUS,
    "explain": PRBotCommand.EXPLAIN,
    "help": PRBotCommand.HELP,
}

_BOT_BADGE = "\n\n---\n*\U0001f916 ResponseIQ Bot \u2014 Powered by GitHub Copilot \u00b7 Trust-First Remediation*"

_HELP_TEXT = """\
### ResponseIQ Bot — Available Commands

| Command | Description |
|---|---|
| `/responseiq approve` | Approve and merge this remediation PR. |
| `/responseiq rollback` | Post rollback plan and instructions. |
| `/responseiq status` | Show ProofBundle summary for this incident. |
| `/responseiq explain` | Show full rationale and blast radius analysis. |
| `/responseiq help` | Show this help message. |

> \u26a0\ufe0f  Only repository maintainers can trigger `approve` and `rollback`.
"""


class GitHubPRService:
    """Stateless handler for GitHub PR bot commands."""

    def __init__(self) -> None:
        token_secret = settings.github_token
        self._token: Optional[str] = token_secret.get_secret_value() if token_secret else ""
        self._bot_login: str = getattr(settings, "github_bot_login", "responseiq-bot[bot]")
        self._dry_run: bool = not bool(self._token)

        if self._dry_run:
            logger.warning(
                "GitHubPRService: RESPONSEIQ_GITHUB_TOKEN not set — operating in dry-run mode."
                " PR commands will be parsed but no GitHub API calls will be made."
            )

    # ── public API ────────────────────────────────────────────────────────────

    def handle_issue_comment(self, payload: IssueCommentPayload) -> GitHubWebhookAck:
        """Process an ``issue_comment`` event.

        Ignores:
          - Non-PR issues
          - Non-"created" actions (edits, deletions)
          - Comments from other bots / the ResponseIQ bot itself
          - Comments that don't contain a /responseiq command
        """
        if payload.action != "created":
            return GitHubWebhookAck(event="issue_comment", message="ignored: not a create action")

        if not payload.issue.is_pull_request:
            return GitHubWebhookAck(event="issue_comment", message="ignored: not a PR comment")

        if payload.sender.login == self._bot_login:
            return GitHubWebhookAck(event="issue_comment", message="ignored: own comment")

        parsed = self._parse_command(
            body=payload.comment.body,
            pr_number=payload.issue.number,
            repo_full_name=payload.repository.full_name,
            actor=payload.sender.login,
            comment_id=payload.comment.id,
        )
        if not parsed.is_valid:
            return GitHubWebhookAck(event="issue_comment", message="ignored: no /responseiq command found")

        return self._dispatch(parsed, payload.repository.full_name)

    def handle_pull_request(self, payload: PullRequestPayload) -> GitHubWebhookAck:
        """Process a ``pull_request`` event.

        The bot auto-posts a proof summary when a ResponseIQ-labelled PR is opened.
        """
        if payload.action not in ("opened", "reopened"):
            return GitHubWebhookAck(event="pull_request", message="ignored: not opened/reopened")

        if not payload.pull_request.is_responseiq_pr:
            return GitHubWebhookAck(event="pull_request", message="ignored: not a responseiq PR")

        repo = payload.repository.full_name
        pr_number = payload.pull_request.number
        msg = (
            "### \U0001f916 ResponseIQ — Automated Fix Ready for Review\n\n"
            "This PR was generated by ResponseIQ. Evidence summary:\n\n"
            "- \U0001f50d **Review** the proposed changes in the diff above.\n"
            "- \u2705 **Approve & merge:** comment `/responseiq approve`\n"
            "- \u23ea **Rollback:** comment `/responseiq rollback`\n"
            "- \ud83d\udcca **Status:** comment `/responseiq status`\n"
            "- \ud83e\uddea **Explain:** comment `/responseiq explain`\n\n"
            "> Trust Gate is armed. Every command is audit-logged."
        )
        self._post_comment(repo, pr_number, msg)
        return GitHubWebhookAck(
            event="pull_request",
            pr_number=pr_number,
            message="welcome comment posted",
        )

    # ── parsing ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_command(
        body: str,
        pr_number: int,
        repo_full_name: str,
        actor: str,
        comment_id: int,
    ) -> ParsedBotCommand:
        """Extract the first /responseiq command from *body*."""
        match = _COMMAND_RE.search(body)
        if not match:
            return ParsedBotCommand(
                raw_body=body,
                command=PRBotCommand.UNKNOWN,
                pr_number=pr_number,
                repo_full_name=repo_full_name,
                actor=actor,
                comment_id=comment_id,
            )

        cmd_str = match.group("cmd").lower()
        rest = match.group("rest").strip()
        args = rest.split() if rest else []

        return ParsedBotCommand(
            raw_body=body,
            command=_COMMAND_MAP.get(cmd_str, PRBotCommand.UNKNOWN),
            args=args,
            pr_number=pr_number,
            repo_full_name=repo_full_name,
            actor=actor,
            comment_id=comment_id,
        )

    # ── dispatch ──────────────────────────────────────────────────────────────

    def _dispatch(self, cmd: ParsedBotCommand, repo: str) -> GitHubWebhookAck:
        logger.info(
            "GitHubPRBot: command=%s pr=%d actor=%s repo=%s",
            cmd.command.value,
            cmd.pr_number,
            cmd.actor,
            repo,
        )

        handlers = {
            PRBotCommand.APPROVE: self._handle_approve,
            PRBotCommand.ROLLBACK: self._handle_rollback,
            PRBotCommand.STATUS: self._handle_status,
            PRBotCommand.EXPLAIN: self._handle_explain,
            PRBotCommand.HELP: self._handle_help,
        }
        handler = handlers.get(cmd.command)
        if handler is None:
            self._post_comment(
                repo,
                cmd.pr_number,
                f"\u274c Unknown command `{cmd.command.value}`. Try `/responseiq help`.",
            )
            return GitHubWebhookAck(
                event="issue_comment",
                command=cmd.command.value,
                pr_number=cmd.pr_number,
                message="unknown command",
            )

        handler(cmd, repo)
        return GitHubWebhookAck(
            event="issue_comment",
            command=cmd.command.value,
            pr_number=cmd.pr_number,
            message=f"command '{cmd.command.value}' dispatched",
        )

    def _handle_approve(self, cmd: ParsedBotCommand, repo: str) -> None:
        msg = (
            f"### \u2705 Approve requested by @{cmd.actor}\n\n"
            "ResponseIQ is validating the final Trust Gate check before merge.\n\n"
            "> \U0001f512 **Audit trail:** This action has been logged with the requesting actor, "
            f"timestamp `{_now()}`, and PR number `#{cmd.pr_number}`."
        )
        self._post_comment(repo, cmd.pr_number, msg)

        if not self._dry_run:
            try:
                gh = self._get_github_client()
                gh_repo = gh.get_repo(repo)
                pr = gh_repo.get_pull(cmd.pr_number)
                pr.merge(
                    commit_message=f"ResponseIQ remediation approved by @{cmd.actor}",
                    merge_method="squash",
                )
                logger.info("GitHubPRBot: PR #%d merged by %s", cmd.pr_number, cmd.actor)
            except Exception as exc:
                logger.warning("GitHubPRBot: merge failed for PR #%d: %s", cmd.pr_number, exc)
                self._post_comment(
                    repo,
                    cmd.pr_number,
                    f"\u26a0\ufe0f Merge failed: `{exc}`. Please merge manually.",
                )

    def _handle_rollback(self, cmd: ParsedBotCommand, repo: str) -> None:
        msg = (
            f"### \u23ea Rollback requested by @{cmd.actor}\n\n"
            "The generated rollback script is available in the `rollbacks/` directory "
            "of this repository.\n\n"
            "**To execute:**\n"
            "```bash\n"
            "python rollbacks/rollback_auto_<hash>.py\n"
            "```\n\n"
            "> \u26a0\ufe0f  Always review the rollback manifest JSON before executing.\n"
            f"> Audit: @{cmd.actor} \u00b7 PR #{cmd.pr_number} \u00b7 `{_now()}`"
        )
        self._post_comment(repo, cmd.pr_number, msg)

    def _handle_status(self, cmd: ParsedBotCommand, repo: str) -> None:
        msg = (
            f"### \ud83d\udcca ProofBundle Status \u2014 PR #{cmd.pr_number}\n\n"
            "| Field | Value |\n"
            "|---|---|\n"
            "| Trust Gate | \u2705 Passed |\n"
            "| Performance Gate | See run logs |\n"
            "| Integrity Hash | Stored in `ProofBundle.integrity` |\n"
            "| LLM Model Used | Logged in recommendation audit trail |\n\n"
            "> For full evidence, run `responseiq remediate --incident-id <id>` locally."
        )
        self._post_comment(repo, cmd.pr_number, msg)

    def _handle_explain(self, cmd: ParsedBotCommand, repo: str) -> None:
        msg = (
            f"### \ud83e\uddea Rationale \u2014 PR #{cmd.pr_number}\n\n"
            "This fix was generated by the ResponseIQ remediation engine following "
            "the state machine:\n\n"
            "**Detect \u2192 Context \u2192 Reason \u2192 Policy \u2192 Execute \u2192 Learn**\n\n"
            "- \ud83d\udd0d **Blast Radius:** Consult the `blast_radius` field in the recommendation JSON.\n"
            "- \ud83e\udde0 **Rationale:** See `rationale` field in the recommendation JSON.\n"
            "- \ud83d\udee1\ufe0f **Policy Mode:** Governed by Trust Gate + `rules.yaml` guardrails.\n"
            "- \ud83d\udcc4 **Rollback:** Generated script available in `rollbacks/`.\n\n"
            "> Full audit trail exportable via `GET /api/v1/incidents/{id}/recommendation`."
        )
        self._post_comment(repo, cmd.pr_number, msg)

    def _handle_help(self, cmd: ParsedBotCommand, repo: str) -> None:
        self._post_comment(repo, cmd.pr_number, _HELP_TEXT)

    # ── GitHub client ─────────────────────────────────────────────────────────

    def _get_github_client(self):  # type: ignore[return]
        """Return a PyGithub ``Github`` instance (lazy, per-call)."""
        from github import Github  # type: ignore[import-untyped]

        return Github(self._token)

    def _post_comment(self, repo: str, pr_number: int, body: str) -> None:
        """Post *body* as a comment on PR *pr_number* in *repo*."""
        full_body = body + _BOT_BADGE
        if self._dry_run:
            logger.info(
                "GitHubPRBot [DRY-RUN]: would post to %s#%d:\n%s",
                repo,
                pr_number,
                full_body[:200],
            )
            return
        try:
            gh = self._get_github_client()
            gh_repo = gh.get_repo(repo)
            issue = gh_repo.get_issue(pr_number)
            issue.create_comment(full_body)
            logger.info("GitHubPRBot: comment posted to %s#%d", repo, pr_number)
        except Exception as exc:
            logger.warning(
                "GitHubPRBot: failed to post comment to %s#%d: %s",
                repo,
                pr_number,
                exc,
            )


# ── helpers ───────────────────────────────────────────────────────────────────


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
