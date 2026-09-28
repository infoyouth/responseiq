"""tests/unit/test_github_pr.py

P8: Headless GitHub PR Bot — unit tests.

Coverage:
- ParsedBotCommand: is_valid flag
- GitHubPRService._parse_command: all 5 commands + unknown + no-match
- GitHubPRService.handle_issue_comment: action filter, non-PR filter, bot loop guard, command dispatch
- GitHubPRService.handle_pull_request: action filter, non-responseiq PR filter, responseiq PR welcome
- GitHubPRService dry-run mode: _post_comment logs instead of calling PyGithub
- HMAC: _verify_github_signature: valid, missing, wrong, empty secret (skip)
- GitHubIssue.is_pull_request property
- GitHubPullRequest.label_names + is_responseiq_pr property
"""

from __future__ import annotations

import hashlib
import hmac
from unittest.mock import patch

from responseiq.routers.github_pr import _verify_github_signature
from responseiq.schemas.github_pr import (
    GitHubComment,
    GitHubIssue,
    GitHubPullRequest,
    GitHubRepo,
    GitHubUser,
    IssueCommentPayload,
    PRBotCommand,
    ParsedBotCommand,
    PullRequestPayload,
)
from responseiq.services.github_pr_service import GitHubPRService


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_REPO = GitHubRepo(id=1, name="responseiq", full_name="infoyouth/responseiq")
_USER = GitHubUser(login="sre-alice", id=42)
_BOT = GitHubUser(login="responseiq-bot[bot]", id=99)


def _make_comment(body: str, user: GitHubUser = _USER) -> GitHubComment:
    return GitHubComment(id=1001, body=body, user=user, html_url="https://github.com/pr/1#comment-1001")


def _make_issue(is_pr: bool = True) -> GitHubIssue:
    return GitHubIssue(
        number=42,
        title="Fix: null pointer on /api/remediate",
        state="open",
        pull_request={"url": "https://api.github.com/repos/infoyouth/responseiq/pulls/42"} if is_pr else None,
    )


def _make_pr_payload(action: str = "opened", labels: list = None) -> PullRequestPayload:
    return PullRequestPayload(
        action=action,
        pull_request=GitHubPullRequest(
            number=42,
            title="fix: null pointer",
            state="open",
            labels=labels or [{"name": "responseiq-fix"}],
        ),
        repository=_REPO,
        sender=_USER,
    )


def _service(dry_run: bool = True) -> GitHubPRService:
    """Return a GitHubPRService in dry-run mode (no token)."""
    with patch("responseiq.services.github_pr_service.settings") as mock_settings:
        mock_settings.github_token = None
        mock_settings.github_bot_login = "responseiq-bot[bot]"
        svc = GitHubPRService()
    return svc


# ─────────────────────────────────────────────────────────────────────────────
# Schema property tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGitHubIssue:
    def test_is_pull_request_true(self):
        issue = _make_issue(is_pr=True)
        assert issue.is_pull_request is True

    def test_is_pull_request_false(self):
        issue = _make_issue(is_pr=False)
        assert issue.is_pull_request is False


class TestGitHubPullRequest:
    def test_label_names(self):
        pr = GitHubPullRequest(number=1, title="t", labels=[{"name": "bug"}, {"name": "responseiq"}])
        assert "responseiq" in pr.label_names

    def test_is_responseiq_pr_true(self):
        pr = GitHubPullRequest(number=1, title="t", labels=[{"name": "responseiq-fix"}])
        assert pr.is_responseiq_pr is True

    def test_is_responseiq_pr_false(self):
        pr = GitHubPullRequest(number=1, title="t", labels=[{"name": "bug"}])
        assert pr.is_responseiq_pr is False

    def test_is_responseiq_pr_no_labels(self):
        pr = GitHubPullRequest(number=1, title="t", labels=[])
        assert pr.is_responseiq_pr is False


# ─────────────────────────────────────────────────────────────────────────────
# ParsedBotCommand
# ─────────────────────────────────────────────────────────────────────────────


class TestParsedBotCommand:
    def _cmd(self, cmd: PRBotCommand) -> ParsedBotCommand:
        return ParsedBotCommand(
            raw_body=f"/responseiq {cmd.value}",
            command=cmd,
            pr_number=42,
            repo_full_name="infoyouth/responseiq",
            actor="alice",
            comment_id=1,
        )

    def test_is_valid_known_command(self):
        for cmd in (PRBotCommand.APPROVE, PRBotCommand.ROLLBACK, PRBotCommand.STATUS):
            assert self._cmd(cmd).is_valid is True

    def test_is_valid_false_for_unknown(self):
        assert self._cmd(PRBotCommand.UNKNOWN).is_valid is False


# ─────────────────────────────────────────────────────────────────────────────
# GitHubPRService._parse_command
# ─────────────────────────────────────────────────────────────────────────────


class TestParseCommand:
    def _parse(self, body: str) -> ParsedBotCommand:
        return GitHubPRService._parse_command(
            body=body, pr_number=42, repo_full_name="infoyouth/responseiq", actor="alice", comment_id=1
        )

    def test_approve(self):
        assert self._parse("/responseiq approve").command == PRBotCommand.APPROVE

    def test_rollback(self):
        assert self._parse("/responseiq rollback").command == PRBotCommand.ROLLBACK

    def test_status(self):
        assert self._parse("/responseiq status").command == PRBotCommand.STATUS

    def test_explain(self):
        assert self._parse("/responseiq explain").command == PRBotCommand.EXPLAIN

    def test_help(self):
        assert self._parse("/responseiq help").command == PRBotCommand.HELP

    def test_unknown_subcommand(self):
        cmd = self._parse("/responseiq frobnicate")
        assert cmd.command == PRBotCommand.UNKNOWN
        assert not cmd.is_valid

    def test_no_responseiq_command(self):
        cmd = self._parse("LGTM! Looks good to merge.")
        assert cmd.command == PRBotCommand.UNKNOWN

    def test_inline_command_mid_comment(self):
        """Command anywhere in the comment body is detected."""
        body = "Great work!\n\n/responseiq approve\n\nThanks!"
        assert self._parse(body).command == PRBotCommand.APPROVE

    def test_case_insensitive(self):
        assert self._parse("/RESPONSEIQ APPROVE").command == PRBotCommand.APPROVE

    def test_args_parsed(self):
        cmd = self._parse("/responseiq rollback v2.13.0")
        assert cmd.args == ["v2.13.0"]


# ─────────────────────────────────────────────────────────────────────────────
# GitHubPRService.handle_issue_comment
# ─────────────────────────────────────────────────────────────────────────────


class TestHandleIssueComment:
    def _payload(self, body: str, action: str = "created", is_pr: bool = True, sender: GitHubUser = _USER):
        return IssueCommentPayload(
            action=action,
            issue=_make_issue(is_pr=is_pr),
            comment=_make_comment(body, user=sender),
            repository=_REPO,
            sender=sender,
        )

    def test_ignores_edited_action(self):
        svc = _service()
        ack = svc.handle_issue_comment(self._payload("/responseiq approve", action="edited"))
        assert "ignored" in ack.message

    def test_ignores_non_pr_issue(self):
        svc = _service()
        ack = svc.handle_issue_comment(self._payload("/responseiq approve", is_pr=False))
        assert "ignored" in ack.message

    def test_ignores_own_bot_comment(self):
        svc = _service()
        ack = svc.handle_issue_comment(self._payload("/responseiq help", sender=_BOT))
        assert "ignored" in ack.message

    def test_ignores_no_command(self):
        svc = _service()
        ack = svc.handle_issue_comment(self._payload("LGTM!"))
        assert "ignored" in ack.message

    def test_dispatches_help(self):
        svc = _service()
        ack = svc.handle_issue_comment(self._payload("/responseiq help"))
        assert ack.command == "help"
        assert ack.pr_number == 42

    def test_dispatches_status(self):
        svc = _service()
        ack = svc.handle_issue_comment(self._payload("/responseiq status"))
        assert ack.command == "status"

    def test_dispatches_explain(self):
        svc = _service()
        ack = svc.handle_issue_comment(self._payload("/responseiq explain"))
        assert ack.command == "explain"

    def test_dispatches_rollback(self):
        svc = _service()
        ack = svc.handle_issue_comment(self._payload("/responseiq rollback"))
        assert ack.command == "rollback"

    def test_dispatches_approve_dry_run(self):
        """Approve in dry-run logs but never raises."""
        svc = _service()
        ack = svc.handle_issue_comment(self._payload("/responseiq approve"))
        assert ack.command == "approve"


# ─────────────────────────────────────────────────────────────────────────────
# GitHubPRService.handle_pull_request
# ─────────────────────────────────────────────────────────────────────────────


class TestHandlePullRequest:
    def test_ignores_closed_action(self):
        svc = _service()
        ack = svc.handle_pull_request(_make_pr_payload(action="closed"))
        assert "ignored" in ack.message

    def test_ignores_non_responseiq_pr(self):
        svc = _service()
        ack = svc.handle_pull_request(_make_pr_payload(labels=[{"name": "bug"}]))
        assert "ignored" in ack.message

    def test_welcome_comment_on_responseiq_pr_opened(self):
        svc = _service()
        ack = svc.handle_pull_request(_make_pr_payload(action="opened"))
        assert "welcome comment posted" in ack.message
        assert ack.pr_number == 42

    def test_welcome_comment_on_reopened(self):
        svc = _service()
        ack = svc.handle_pull_request(_make_pr_payload(action="reopened"))
        assert "welcome comment posted" in ack.message


# ─────────────────────────────────────────────────────────────────────────────
# HMAC signature verification
# ─────────────────────────────────────────────────────────────────────────────


class TestVerifyGitHubSignature:
    def _sign(self, secret: str, body: bytes) -> str:
        return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    def test_valid_signature(self):
        body = b'{"action": "created"}'
        sig = self._sign("mysecret", body)
        assert _verify_github_signature("mysecret", body, sig) is True

    def test_invalid_signature(self):
        body = b'{"action": "created"}'
        assert _verify_github_signature("mysecret", body, "sha256=badhash") is False

    def test_missing_sha256_prefix(self):
        body = b"test"
        sig = hmac.new("mysecret".encode(), body, hashlib.sha256).hexdigest()
        assert _verify_github_signature("mysecret", body, sig) is False

    def test_empty_signature_header(self):
        assert _verify_github_signature("mysecret", b"test", "") is False

    def test_empty_secret_skips_check(self):
        """No secret configured → skip verification (dev mode)."""
        assert _verify_github_signature("", b"anything", "sha256=garbage") is True

    def test_tampered_body_fails(self):
        body = b'{"action": "created"}'
        sig = self._sign("mysecret", body)
        tampered = b'{"action": "deleted"}'
        assert _verify_github_signature("mysecret", tampered, sig) is False
