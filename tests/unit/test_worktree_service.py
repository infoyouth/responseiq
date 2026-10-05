import subprocess
import sys

import pytest

from responseiq.services.worktree_service import (
    WorktreePreparationError,
    WorktreePreparationService,
    WorktreeValidationError,
)
from responseiq.utils.git_utils import GitClient


def run_git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def create_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.name", "Test User")
    run_git(repo, "config", "user.email", "test@example.com")
    (repo / "app.txt").write_text("before\n", encoding="utf-8")
    run_git(repo, "add", "app.txt")
    run_git(repo, "commit", "-m", "initial")
    return repo


def test_prepare_and_push_applies_validates_and_cleans_worktree(tmp_path, monkeypatch):
    repo = create_repo(tmp_path)

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


def test_required_checks_run_against_patched_candidate(tmp_path, monkeypatch):
    repo = create_repo(tmp_path)
    (repo / "app.py").write_text("def is_fixed():\n    return False\n", encoding="utf-8")
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text(
        "from app import is_fixed\n\n\ndef test_candidate_patch():\n    assert is_fixed()\n",
        encoding="utf-8",
    )
    run_git(repo, "add", "app.py", "tests/test_app.py")
    run_git(repo, "commit", "-m", "add candidate regression test")
    monkeypatch.setattr(GitClient, "push", lambda *args: True)

    result = WorktreePreparationService().prepare_and_push(
        repo_path=repo,
        repo_name="example/repo",
        patch_text="""diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,2 @@
 def is_fixed():
-    return False
+    return True
""",
        validation_commands=[],
        required_checks=["tests", "security_scan", "syntax_check"],
        token="test-token",
        branch_name="responseiq-required-checks",
    )

    assert run_git(repo, "show", f"{result.branch_name}:app.py") == "def is_fixed():\n    return True\n"


def test_validation_runs_in_hermetic_sandbox(tmp_path, monkeypatch):
    repo = create_repo(tmp_path)
    calls = []

    class FakeSandboxRunner:
        async def run(self, command, *, cwd, environment):
            calls.append({"command": list(command), "cwd": str(cwd), "environment": dict(environment)})
            return type("Result", (), {"returncode": 0, "output": b"ok", "timed_out": False})()

    monkeypatch.setattr(GitClient, "push", lambda *args: True)

    WorktreePreparationService(sandbox_runner=FakeSandboxRunner()).prepare_and_push(
        repo_path=repo,
        repo_name="example/repo",
        patch_text="""diff --git a/app.txt b/app.txt
--- a/app.txt
+++ b/app.txt
@@ -1 +1 @@
-before
+after
""",
        validation_commands=[[sys.executable, "-c", "print('validated')"]],
        token="test-token",
        branch_name="responseiq-hermetic-check",
    )

    assert calls
    assert calls[0]["command"][0] == sys.executable
    assert calls[0]["cwd"] != str(repo)
    assert calls[0]["cwd"].startswith(str(tmp_path))


def test_security_check_includes_new_python_files(tmp_path, monkeypatch):
    repo = create_repo(tmp_path)
    monkeypatch.setattr(GitClient, "push", lambda *args: pytest.fail("invalid candidate must not be pushed"))

    with pytest.raises(WorktreeValidationError, match=r"ruff check --select S unsafe\.py"):
        WorktreePreparationService().prepare_and_push(
            repo_path=repo,
            repo_name="example/repo",
            patch_text="""diff --git a/unsafe.py b/unsafe.py
new file mode 100644
--- /dev/null
+++ b/unsafe.py
@@ -0,0 +1,2 @@
+import subprocess
+subprocess.run("echo unsafe", shell=True)
""",
            validation_commands=[],
            required_checks=["security_scan"],
            token="test-token",
            branch_name="responseiq-new-python-security",
        )


def test_failed_candidate_validation_does_not_push_or_change_checkout(tmp_path, monkeypatch):
    repo = create_repo(tmp_path)
    pushed = []
    monkeypatch.setattr(GitClient, "push", lambda *args: pushed.append(args) or True)

    with pytest.raises(WorktreeValidationError, match="validation command failed"):
        WorktreePreparationService().prepare_and_push(
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
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; assert Path('app.txt').read_text() == 'before\\n'",
                ]
            ],
            token="test-token",
        )

    assert not pushed
    assert (repo / "app.txt").read_text(encoding="utf-8") == "before\n"
    assert not list(tmp_path.glob("responseiq-worktree-*"))


@pytest.mark.parametrize(
    ("patch_text", "validation_commands", "token", "message"),
    [
        ("", [["pytest"]], "token", "non-empty unified diff"),
        ("diff", [], "token", "validation command"),
        ("diff", [["pytest"]], "", "GitHub token"),
    ],
)
def test_prepare_rejects_missing_prerequisites(tmp_path, patch_text, validation_commands, token, message):
    with pytest.raises(WorktreePreparationError, match=message):
        WorktreePreparationService().prepare_and_push(
            repo_path=tmp_path,
            repo_name="example/repo",
            patch_text=patch_text,
            validation_commands=validation_commands,
            token=token,
        )


def test_prepare_rejects_empty_validation_argv(tmp_path):
    repo = create_repo(tmp_path)
    with pytest.raises(WorktreePreparationError, match="non-empty argv"):
        WorktreePreparationService().prepare_and_push(
            repo_path=repo,
            repo_name="example/repo",
            patch_text="""diff --git a/app.txt b/app.txt
--- a/app.txt
+++ b/app.txt
@@ -1 +1 @@
-before
+after
""",
            validation_commands=[["pytest", ""]],
            token="test-token",
        )


def test_prepare_reports_push_failure(tmp_path, monkeypatch):
    repo = create_repo(tmp_path)
    monkeypatch.setattr(GitClient, "push", lambda self, branch_name, token, repo_slug: False)
    with pytest.raises(WorktreePreparationError, match="push"):
        WorktreePreparationService().prepare_and_push(
            repo_path=repo,
            repo_name="example/repo",
            patch_text="""diff --git a/app.txt b/app.txt
--- a/app.txt
+++ b/app.txt
@@ -1 +1 @@
-before
+after
""",
            validation_commands=[[sys.executable, "-c", "pass"]],
            token="test-token",
            branch_name="responseiq-push-failure",
        )


def test_run_wraps_git_errors(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0], stderr="bad command")

    monkeypatch.setattr("responseiq.services.worktree_service.subprocess.run", fail)
    with pytest.raises(WorktreePreparationError, match="git command failed.*bad command"):
        WorktreePreparationService._run_git(tmp_path, ["status"])


def test_remove_worktree_logs_cleanup_failure(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0], stderr="cannot remove")

    monkeypatch.setattr("responseiq.services.worktree_service.subprocess.run", fail)
    WorktreePreparationService._remove_worktree(tmp_path, tmp_path / "missing-worktree")
