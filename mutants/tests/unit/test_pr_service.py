from unittest.mock import MagicMock

from responseiq.services.pr_service import PRService


def test_create_prepared_draft_pr_uses_draft_flag() -> None:
    service = PRService()
    service.gh = MagicMock()
    service.gh.create_pr.return_value = "https://github.com/example/repo/pull/42"

    result = service.create_prepared_draft_pr(
        repo_name="example/repo",
        branch_name="responseiq-fix-42",
        title="fix: repair incident",
        body="Validated remediation evidence.",
    )

    assert result == "https://github.com/example/repo/pull/42"
    service.gh.create_pr.assert_called_once_with(
        repo_name="example/repo",
        title="fix: repair incident",
        body="Validated remediation evidence.",
        head="responseiq-fix-42",
        base="main",
        draft=True,
    )
