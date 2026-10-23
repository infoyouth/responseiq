"""Bounded subprocess execution for generated reproduction tests."""

from __future__ import annotations

import asyncio
import os
import shutil
import signal
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

try:
    import resource
except ImportError:  # pragma: no cover - exercised only on non-POSIX hosts
    resource = None  # type: ignore[assignment]

_SANDBOX_TMP = os.path.join(os.sep, "tmp")
_SANDBOX_HOME = os.path.join(_SANDBOX_TMP, "home")
_SANDBOX_WORKSPACE = os.path.join(_SANDBOX_TMP, "workspace")

_SYSTEM_MOUNTS = ("/usr", "/bin", "/sbin", "/lib", "/lib64")


class SandboxExecutionError(RuntimeError):
    """Raised when the requested sandbox boundary cannot be established."""


@dataclass(frozen=True)
class SandboxLimits:
    """Resource and network policy for one generated-code execution."""

    timeout_seconds: float = 30.0
    cpu_seconds: int = 10
    memory_bytes: int | None = 2 * 1024 * 1024 * 1024
    process_count: int | None = 1024
    disk_bytes: int = 1024 * 1024 * 1024
    network_disabled: bool = True
    allowed_environment: tuple[str, ...] = (
        "PATH",
        "PYTHONPATH",
        "PYTHONNOUSERSITE",
    )


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
        if self.limits.disk_bytes <= 0:
            raise SandboxExecutionError("Sandbox disk limit must be positive")
        if not cwd.is_dir():
            raise SandboxExecutionError(f"Sandbox working directory does not exist: {cwd}")

        safe_environment = {
            key: value for key, value in (environment or os.environ).items() if key in self.limits.allowed_environment
        }

        bwrap = shutil.which("bwrap")
        if not bwrap:
            raise SandboxExecutionError("Bubblewrap is required; refusing to execute without filesystem isolation")

        safe_environment.update(
            {
                "PATH": os.pathsep.join(
                    [
                        str(Path(sys.prefix) / "bin"),
                        "/usr/local/bin",
                        "/usr/bin",
                        "/bin",
                    ]
                ),
                "HOME": _SANDBOX_HOME,
                "TMPDIR": _SANDBOX_TMP,
                "PYTHONPATH": os.path.join(_SANDBOX_WORKSPACE, "src"),
                "PYTHONNOUSERSITE": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )

        bounded_command = [self._rewrite_candidate_path(part, cwd) for part in command]

        if self.limits.process_count is not None:
            bounded_command = [
                str(Path(sys.prefix) / "bin" / "python"),
                "-c",
                (
                    "import os, resource, sys; "
                    "limit = int(sys.argv[1]); "
                    "resource.setrlimit(resource.RLIMIT_NPROC, (limit, limit)); "
                    "os.execvp(sys.argv[2], sys.argv[2:])"
                ),
                str(self.limits.process_count),
                *bounded_command,
            ]

        wrapped_command = self._build_command(bwrap, bounded_command, cwd, safe_environment)

        process = await asyncio.create_subprocess_exec(
            *wrapped_command,
            cwd=Path("/"),
            env={},
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
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            output, _ = await process.communicate()
            output += (f"\n[ResponseIQ] Execution TIMED OUT after {self.limits.timeout_seconds}s.").encode()

        return SandboxResult(
            returncode=process.returncode,
            output=output,
            timed_out=timed_out,
            command=wrapped_command,
        )

    def _build_command(
        self,
        bwrap: str,
        command: list[str],
        cwd: Path,
        environment: Mapping[str, str],
    ) -> list[str]:
        args = [
            bwrap,
            "--unshare-user",
            "--unshare-pid",
            "--unshare-uts",
            "--unshare-ipc",
            "--die-with-parent",
            "--new-session",
            "--cap-drop",
            "ALL",
        ]

        if self.limits.network_disabled:
            args.append("--unshare-net")

        for system_path in _SYSTEM_MOUNTS:
            if Path(system_path).exists():
                args.extend(["--ro-bind", system_path, system_path])

        args.extend(
            [
                "--size",
                str(min(self.limits.disk_bytes, 64 * 1024 * 1024)),
                "--tmpfs",
                "/home",
                "--size",
                str(self.limits.disk_bytes),
                "--tmpfs",
                _SANDBOX_TMP,
                "--tmpfs",
                "/etc",
            ]
        )

        for system_config in (
            "/etc/passwd",
            "/etc/group",
            "/etc/localtime",
            "/etc/ssl/certs",
        ):
            if Path(system_config).exists():
                args.extend(["--ro-bind-try", system_config, system_config])

        args.extend(["--dev", "/dev", "--proc", "/proc"])

        prefix_paths = {
            Path(sys.prefix),
            Path(sys.base_prefix),
        }

        # A venv's python executable can point through a symlinked
        # interpreter directory. Mount that alias path too, so the
        # interpreter can resolve its executable inside Bubblewrap.
        venv_python = Path(sys.prefix) / "bin" / "python"
        if venv_python.is_symlink():
            python_target = Path(os.readlink(venv_python))
            if not python_target.is_absolute():
                python_target = venv_python.parent / python_target

            prefix_paths.add(python_target.parent.parent)

        created_dirs: set[str] = set()
        for prefix in sorted(prefix_paths, key=lambda path: len(path.parts)):
            if prefix.exists():
                self._add_readonly_mount(args, prefix, created_dirs)

        args.extend(
            [
                "--ro-bind",
                str(cwd.resolve()),
                "/candidate",
                "--dir",
                _SANDBOX_HOME,
                "--dir",
                _SANDBOX_WORKSPACE,
                "--clearenv",
            ]
        )

        for key, value in environment.items():
            args.extend(["--setenv", key, value])

        args.extend(
            [
                "--chdir",
                _SANDBOX_TMP,
                "/bin/sh",
                "-c",
                ('cp -a /candidate/. /tmp/workspace/ && rm -rf /tmp/workspace/.git && cd /tmp/workspace && exec "$@"'),
                "responseiq-sandbox",
                *command,
            ]
        )
        return args

    @staticmethod
    def _add_readonly_mount(
        args: list[str],
        source: Path,
        created_dirs: set[str],
    ) -> None:
        """Mount a path read-only, creating missing destination parents."""
        target = str(source)

        for parent in reversed(source.parents):
            parent_text = str(parent)

            if parent_text == "/":
                continue

            # These locations already exist because their parent system
            # filesystem has been mounted, or because /home is a tmpfs.
            if any(parent == Path(root) or parent.is_relative_to(Path(root)) for root in _SYSTEM_MOUNTS):
                continue

            if parent == Path("/home"):
                continue

            if parent_text not in created_dirs:
                args.extend(["--dir", parent_text])
                created_dirs.add(parent_text)

        args.extend(["--ro-bind", target, target])

    @staticmethod
    def _rewrite_candidate_path(value: str, cwd: Path) -> str:
        candidate = str(cwd.resolve())
        if value == candidate:
            return _SANDBOX_WORKSPACE
        if value.startswith(candidate + os.sep):
            return _SANDBOX_WORKSPACE + value[len(candidate) :]
        return value

    def _apply_limits(self) -> None:
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (self.limits.cpu_seconds, self.limits.cpu_seconds),
        )
        if self.limits.memory_bytes is not None:
            resource.setrlimit(
                resource.RLIMIT_AS,
                (self.limits.memory_bytes, self.limits.memory_bytes),
            )
