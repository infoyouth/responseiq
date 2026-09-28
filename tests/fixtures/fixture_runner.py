"""Reusable helpers for hermetic before/after incident fixture tests."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FixtureSpec:
    """Source and contract metadata for one incident regression fixture."""

    source_path: Path
    fixture_dir: Path

    @property
    def expected(self) -> dict[str, object]:
        return json.loads((self.fixture_dir / "expected.json").read_text(encoding="utf-8"))


class FixtureRunner:
    """Prepare patched or unpatched fixture copies and run bounded scripts."""

    def __init__(self, spec: FixtureSpec, timeout_seconds: int = 10) -> None:
        self.spec = spec
        self.timeout_seconds = timeout_seconds

    def prepare(self, root: Path, *, patched: bool = False, name: str | None = None) -> Path:
        module_dir = root / (name or self.spec.fixture_dir.name)
        module_dir.mkdir()
        (module_dir / self.spec.source_path.name).write_bytes(self.spec.source_path.read_bytes())
        if patched:
            self.apply_patch(module_dir)
        return module_dir

    def apply_patch(self, module_dir: Path) -> None:
        self.run_command(
            ["git", "apply", "--unidiff-zero", str(self.spec.fixture_dir / "expected.patch")],
            cwd=module_dir,
            check=True,
        )

    def run(self, module_dir: Path, script: str) -> subprocess.CompletedProcess[str]:
        return self.run_command([sys.executable, "-c", script], cwd=module_dir, check=False)

    def run_command(self, command: list[str], *, cwd: Path, check: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check,
            timeout=self.timeout_seconds,
        )
