"""src/responseiq/routers/github_pr.py

P8: Headless PR Interventions — GitHub App webhook endpoint.

Endpoint
─────────
POST /webhooks/github

GitHub sends ALL app event types to this single URL.  The router
dispatches on the ``X-GitHub-Event`` header:

    ping            → acknowledge (confirms webhook is live)
    issue_comment   → parse /responseiq commands typed on PR comments
    pull_request    → auto-post proof summary on ResponseIQ-labelled PRs

Signature Verification
──────────────────────
GitHub signs every delivery with HMAC-SHA256 using the webhook secret
configured in the GitHub App settings.  The signature is sent in the
``X-Hub-Signature-256`` header as ``sha256=<hex>``.

Configure via:
    RESPONSEIQ_GITHUB_WEBHOOK_SECRET=<your_app_webhook_secret>

When the secret is **not** set, signature verification is skipped
(safe for local development; never skip in production).
"""

from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import ValidationError

from ..schemas.github_pr import (
    GitHubEventType,
    GitHubWebhookAck,
    IssueCommentPayload,
    PullRequestPayload,
)
from ..services.github_pr_service import GitHubPRService
from ..utils.logger import logger

router = APIRouter(prefix="/webhooks", tags=["github-pr-bot"])


# ── HMAC helper ───────────────────────────────────────────────────────────────


def _verify_github_signature(secret: str, raw_body: bytes, signature_header: str) -> bool:
    """Return True if the HMAC-SHA256 signature matches."""
    if not secret:
        return True  # dev mode — skip
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


# ── endpoint ─────────────────────────────────────────────────────────────────


@router.post("/github", response_model=GitHubWebhookAck, status_code=200)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default="unknown", alias="X-GitHub-Event"),
    x_hub_signature_256: str = Header(default="", alias="X-Hub-Signature-256"),
) -> GitHubWebhookAck:
    """
    Receive GitHub App webhook events and dispatch to the PR bot.

    All unrecognised event types receive a 200 "ignored" response so
    GitHub doesn't mark the delivery as failed.
    """
    from ..config.settings import settings

    raw_body = await request.body()

    # ── signature verification ────────────────────────────────────────────────
    webhook_secret_raw = getattr(settings, "github_webhook_secret", None)
    webhook_secret: str = webhook_secret_raw.get_secret_value() if webhook_secret_raw else ""
    if not _verify_github_signature(webhook_secret, raw_body, x_hub_signature_256):
        logger.warning("GitHub webhook: invalid HMAC-SHA256 signature — rejecting")
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    logger.info("GitHub webhook received: event=%s", x_github_event)

    # ── dispatch ──────────────────────────────────────────────────────────────
    event_type = (
        GitHubEventType(x_github_event)
        if x_github_event in GitHubEventType._value2member_map_
        else GitHubEventType.UNKNOWN
    )
    service = GitHubPRService()

    if event_type == GitHubEventType.PING:
        return GitHubWebhookAck(event="ping", message="pong — ResponseIQ webhook is live")

    if event_type == GitHubEventType.ISSUE_COMMENT:
        try:
            ic_payload = IssueCommentPayload.model_validate(await request.json())
        except ValidationError as exc:
            logger.warning("GitHub webhook: invalid issue_comment payload: %s", exc)
            raise HTTPException(status_code=422, detail="Invalid issue_comment payload") from exc
        return service.handle_issue_comment(ic_payload)

    if event_type == GitHubEventType.PULL_REQUEST:
        try:
            pr_payload = PullRequestPayload.model_validate(await request.json())
        except ValidationError as exc:
            logger.warning("GitHub webhook: invalid pull_request payload: %s", exc)
            raise HTTPException(status_code=422, detail="Invalid pull_request payload") from exc
        return service.handle_pull_request(pr_payload)

    # All other event types — acknowledge without processing
    return GitHubWebhookAck(
        event=x_github_event,
        message=f"event '{x_github_event}' acknowledged but not handled",
    )
