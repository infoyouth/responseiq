import subprocess
import sys

from responseiq.services.worktree_service import WorktreePreparationService
from responseiq.utils.git_utils import GitClient


def run_git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def test_prepare_and_push_applies_validates_and_cleans_worktree(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.name", "Test User")
    run_git(repo, "config", "user.email", "test@example.com")
    (repo / "app.txt").write_text("before\n", encoding="utf-8")
    run_git(repo, "add", "app.txt")
    run_git(repo, "commit", "-m", "initial")

    pushed = {}

    def fake_push(self, branch_name, token, repo_slug):
        pushed.update(branch=branch_name, token=token, repo=repo_slug)
        return True

    monkeypatch.setattr(GitClient, "push", fake_push)

    result = WorktreePreparationService().prepare_and_push(
        repo_path=repo,
        repo_name="example/repo",
        patch_text="""diff --git a/app.txt b/app.txt
--- a/app.txt
+++ b/app.txt
@@ -1 +1 @@
-before
+after
""",
        validation_commands=[
            [sys.executable, "-c", "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'"]
        ],
        token="test-token",
        branch_name="responseiq-test-fix",
    )

    assert result.branch_name == "responseiq-test-fix"
    assert len(result.commit_sha) == 40
    assert pushed == {
        "branch": "responseiq-test-fix",
        "token": "test-token",
        "repo": "example/repo",
    }
    assert (repo / "app.txt").read_text(encoding="utf-8") == "before\n"
    assert not list(tmp_path.glob("responseiq-worktree-*"))
    assert run_git(repo, "show", "responseiq-test-fix:app.txt") == "after\n"
