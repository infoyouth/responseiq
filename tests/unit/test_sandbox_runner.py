import shutil
import socket
import subprocess
import sys

import pytest

from responseiq.services.sandbox_runner import SandboxExecutionError, SandboxLimits, SandboxRunner


def _require_bwrap():
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
    return bwrap


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
    _require_bwrap()

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


@pytest.mark.asyncio
async def test_network_disabled_sandbox_cannot_reach_host_listener(tmp_path):
    _require_bwrap()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        result = await SandboxRunner().run(
            [
                sys.executable,
                "-c",
                "import socket, sys; "
                "s = socket.socket(); "
                "s.settimeout(0.5); "
                "\ntry: s.connect(('127.0.0.1', int(sys.argv[1])))\n"
                "except OSError: print('network blocked')\n"
                "else: raise SystemExit('host network reachable')",
                str(port),
            ],
            cwd=tmp_path,
        )

    assert result.returncode == 0, result.output.decode(errors="replace")
    assert result.output.strip() == b"network blocked"


@pytest.mark.asyncio
async def test_sandbox_enforces_cpu_limit(tmp_path):
    _require_bwrap()
    result = await SandboxRunner(
        SandboxLimits(timeout_seconds=5, cpu_seconds=1, memory_bytes=2 * 1024**3, process_count=1024)
    ).run([sys.executable, "-c", "while True: pass"], cwd=tmp_path)

    assert result.timed_out is False
    assert result.returncode != 0


@pytest.mark.asyncio
async def test_sandbox_caps_address_space(tmp_path):
    _require_bwrap()
    result = await SandboxRunner(SandboxLimits(memory_bytes=128 * 1024 * 1024, process_count=1024)).run(
        [
            sys.executable,
            "-c",
            "try:\n"
            "    bytearray(512 * 1024 * 1024)\n"
            "except MemoryError:\n"
            "    print('memory bound enforced')\n"
            "else:\n"
            "    raise SystemExit('memory limit not enforced')\n",
        ],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.output.decode(errors="replace")
    assert result.output.strip() == b"memory bound enforced"


@pytest.mark.asyncio
async def test_sandbox_caps_process_creation(tmp_path):
    _require_bwrap()
    result = await SandboxRunner(
        SandboxLimits(timeout_seconds=8, cpu_seconds=5, process_count=64, memory_bytes=512 * 1024 * 1024)
    ).run(
        [
            sys.executable,
            "-c",
            "import subprocess, sys\n"
            "children = []\n"
            "try:\n"
            "    for _ in range(128):\n"
            "        children.append(subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)']))\n"
            "except OSError:\n"
            "    print('process bound enforced')\n"
            "else:\n"
            "    raise SystemExit('process limit not enforced')\n"
            "finally:\n"
            "    for child in children:\n"
            "        child.terminate()\n"
            "        child.wait()\n",
        ],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.output.decode(errors="replace")
    assert result.output.strip() == b"process bound enforced"


@pytest.mark.asyncio
async def test_sandbox_caps_writable_workspace_disk(tmp_path):
    _require_bwrap()
    result = await SandboxRunner(
        SandboxLimits(disk_bytes=8 * 1024 * 1024, memory_bytes=2 * 1024**3, process_count=1024)
    ).run(
        [
            sys.executable,
            "-c",
            "from pathlib import Path\n"
            "try:\n"
            "    Path('/tmp/workspace/disk-probe').write_bytes(b'x' * 16 * 1024 * 1024)\n"
            "except OSError:\n"
            "    print('disk bound enforced')\n"
            "else:\n"
            "    raise SystemExit('workspace disk limit not enforced')\n",
        ],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.output.decode(errors="replace")
    assert result.output.strip() == b"disk bound enforced"
