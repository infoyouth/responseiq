"""Bounded subprocess execution for generated reproduction tests."""

from __future__ import annotations

import asyncio
import os
import shutil
import signal
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

try:
    import resource
except ImportError:  # pragma: no cover - exercised only on non-POSIX hosts
    resource = None  # type: ignore[assignment]


class SandboxExecutionError(RuntimeError):
    """Raised when the requested sandbox boundary cannot be established."""


@dataclass(frozen=True)
class SandboxLimits:
    """Resource and network policy for one generated-code execution."""

    timeout_seconds: float = 30.0
    cpu_seconds: int = 10
    memory_bytes: int | None = None
    process_count: int | None = None
    network_disabled: bool = True
    allowed_environment: tuple[str, ...] = ("PATH", "PYTHONPATH", "PYTHONNOUSERSITE")


@dataclass
class SandboxResult:
    """Captured bounded subprocess outcome."""

    returncode: int | None
    output: bytes
    timed_out: bool = False
    command: list[str] = field(default_factory=list)


class SandboxRunner:
    """Execute an argv command with least-privilege process boundaries."""

    def __init__(self, limits: SandboxLimits | None = None) -> None:
        self.limits = limits or SandboxLimits()

    async def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str] | None = None,
    ) -> SandboxResult:
        if not command or any(not part for part in command):
            raise SandboxExecutionError("Sandbox commands must contain non-empty argv entries")
        if os.name != "posix" or resource is None:
            raise SandboxExecutionError("Sandbox resource limits require a POSIX host")

        safe_environment = {
            key: value for key, value in (environment or os.environ).items() if key in self.limits.allowed_environment
        }
        safe_environment.setdefault("PYTHONNOUSERSITE", "1")
        bounded_command = list(command)
        if self.limits.network_disabled:
            unshare = shutil.which("unshare")
            if not unshare:
                raise SandboxExecutionError("Network-disabled sandbox requires the unshare executable")
            bounded_command = [unshare, "--net", "--", *bounded_command]

        process = await asyncio.create_subprocess_exec(
            *bounded_command,
            cwd=cwd,
            env=safe_environment,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
            preexec_fn=self._apply_limits,
        )
        timed_out = False
        try:
            output, _ = await asyncio.wait_for(process.communicate(), self.limits.timeout_seconds)
        except asyncio.TimeoutError:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            output, _ = await process.communicate()
            output += f"\n[ResponseIQ] Execution TIMED OUT after {self.limits.timeout_seconds}s.".encode()

        return SandboxResult(
            returncode=process.returncode,
            output=output,
            timed_out=timed_out,
            command=bounded_command,
        )

    def _apply_limits(self) -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (self.limits.cpu_seconds, self.limits.cpu_seconds))
        if self.limits.memory_bytes is not None:
            resource.setrlimit(resource.RLIMIT_AS, (self.limits.memory_bytes, self.limits.memory_bytes))
        if self.limits.process_count is not None:
            resource.setrlimit(resource.RLIMIT_NPROC, (self.limits.process_count, self.limits.process_count))
