import shutil
import subprocess
import sys

import pytest

from responseiq.services.sandbox_runner import SandboxExecutionError, SandboxLimits, SandboxRunner


@pytest.mark.asyncio
async def test_runner_strips_unapproved_environment(tmp_path):
    runner = SandboxRunner(SandboxLimits(network_disabled=False))
    result = await runner.run(
        [sys.executable, "-c", "import os; print('SECRET' in os.environ)"],
        cwd=tmp_path,
        environment={"PATH": "/usr/bin", "SECRET": "do-not-leak"},
    )

    assert result.returncode == 0
    assert result.output.strip() == b"False"


@pytest.mark.asyncio
async def test_runner_kills_timed_out_process(tmp_path):
    runner = SandboxRunner(SandboxLimits(timeout_seconds=0.05, network_disabled=False))
    result = await runner.run(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        cwd=tmp_path,
    )

    assert result.timed_out is True
    assert result.returncode != 0
    assert b"TIMED OUT" in result.output


@pytest.mark.asyncio
async def test_network_disabled_runner_fails_closed_without_unshare(tmp_path, monkeypatch):
    monkeypatch.setattr("responseiq.services.sandbox_runner.shutil.which", lambda _: None)
    runner = SandboxRunner()

    with pytest.raises(SandboxExecutionError, match="Bubblewrap"):
        await runner.run([sys.executable, "-c", "pass"], cwd=tmp_path)


@pytest.mark.asyncio
async def test_runner_hides_host_files_and_uses_disposable_workspace(tmp_path):
    bwrap = shutil.which("bwrap")
    if bwrap is None:
        pytest.skip("bubblewrap is unavailable")
    probe = subprocess.run(
        [
            bwrap,
            "--unshare-user",
            "--unshare-net",
            "--die-with-parent",
            "--ro-bind",
            "/",
            "/",
            "--",
            "/usr/bin/true",
        ],
        capture_output=True,
        check=False,
    )
    if probe.returncode != 0:
        pytest.skip("bubblewrap namespaces are unavailable")

    candidate = tmp_path / "candidate"
    candidate.mkdir()
    outside_secret = tmp_path / "host-secret.txt"
    outside_secret.write_text("host secret", encoding="utf-8")
    (candidate / "candidate.txt").write_text("before", encoding="utf-8")

    result = await SandboxRunner().run(
        [
            sys.executable,
            "-c",
            "from pathlib import Path; "
            f"print(Path({str(outside_secret)!r}).exists()); "
            "print(Path('/etc/shadow').exists()); "
            "Path('candidate.txt').write_text('changed')",
        ],
        cwd=candidate,
        environment={"PATH": "/usr/bin", "SECRET": "do-not-leak"},
    )

    assert result.returncode == 0, result.output.decode(errors="replace")
    assert result.output.splitlines() == [b"False", b"False"]
    assert (candidate / "candidate.txt").read_text(encoding="utf-8") == "before"
