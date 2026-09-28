"""Run pip-audit with bounded retries for transient package-index failures."""

from __future__ import annotations

import argparse
import subprocess
import time
from collections.abc import Callable, Sequence
from pathlib import Path

TRANSIENT_MARKERS = (
    "502 bad gateway",
    "503 service unavailable",
    "503 server error",
    "504 gateway timeout",
    "backend is unhealthy",
    "connectionerror",
    "connection reset",
    "temporarily unavailable",
)


def run_audit(
    output_path: Path,
    *,
    retries: int = 3,
    delay_seconds: int = 20,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    command = [
        "uv",
        "run",
        "pip-audit",
        "--format",
        "cyclonedx-json",
        "-o",
        str(output_path),
    ]
    for attempt in range(1, retries + 1):
        result = runner(command, capture_output=True, text=True, check=False)
        combined_output = f"{result.stdout}\n{result.stderr}"
        print(combined_output, end="")
        if result.returncode == 0:
            return 0

        transient = any(marker in combined_output.lower() for marker in TRANSIENT_MARKERS)
        if not transient or attempt == retries:
            return result.returncode
        print(f"pip-audit service failure; retrying ({attempt}/{retries})")
        sleep(delay_seconds)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--delay-seconds", type=int, default=20)
    args = parser.parse_args(argv)
    return run_audit(args.output, retries=args.retries, delay_seconds=args.delay_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
