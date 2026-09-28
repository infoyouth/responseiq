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

    with pytest.raises(SandboxExecutionError, match="unshare"):
        await runner.run([sys.executable, "-c", "pass"], cwd=tmp_path)
