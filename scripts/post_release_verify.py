"""Verify a local or published ResponseIQ distribution after release."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from subprocess import CompletedProcess
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PACKAGE_NAME = "responseiq"
VENV_PATH = Path("/tmp/responseiq-post")


def _run(command: list[str], *, check: bool = True) -> CompletedProcess[str]:
    return subprocess.run(command, check=check, text=True)


def _pypi_wheel_url(version: str, opener: Callable[..., object] = urlopen) -> str:
    request = Request(
        f"https://pypi.org/pypi/{PACKAGE_NAME}/{version}/json",
        headers={"Cache-Control": "no-cache"},
    )
    with opener(request, timeout=15) as response:  # type: ignore[arg-type]
        metadata = json.load(response)
    for file_info in metadata.get("urls", []):
        if file_info.get("filename", "").endswith("-py3-none-any.whl"):
            return str(file_info["url"])
    raise RuntimeError(f"PyPI metadata has no universal wheel for {PACKAGE_NAME}=={version}")


def _resolve_pypi_wheel(
    version: str,
    *,
    retries: int = 8,
    delay_seconds: int = 20,
    opener: Callable[..., object] = urlopen,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        print(f"Resolve PyPI metadata attempt {attempt} for {PACKAGE_NAME}=={version}")
        try:
            return _pypi_wheel_url(version, opener)
        except (OSError, HTTPError, URLError, KeyError, RuntimeError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                sleep(delay_seconds)
    raise RuntimeError(f"Unable to resolve {PACKAGE_NAME}=={version} from PyPI") from last_error


def _target_python() -> Path:
    return VENV_PATH / "bin" / "python"


def _create_environment() -> None:
    if VENV_PATH.exists():
        shutil.rmtree(VENV_PATH)
    _run(["uv", "venv", str(VENV_PATH), "--python", sys.executable])


def _install_local(version: str, dist_dir: Path) -> None:
    _run(["uv", "build", "--out-dir", str(dist_dir)])
    wheels = sorted(dist_dir.glob(f"{PACKAGE_NAME}-{version}-*.whl"))
    if not wheels:
        raise RuntimeError(f"No wheel found for {PACKAGE_NAME}=={version} in {dist_dir}")
    _run(["uv", "pip", "install", "--python", str(_target_python()), str(wheels[-1])])


def _install_pypi(version: str) -> None:
    package_url = _resolve_pypi_wheel(version)
    _run(["uv", "pip", "install", "--python", str(_target_python()), "--no-cache", package_url])
    print(f"Installed exact PyPI artifact: {package_url}")


def _verify_installed_version(expected: str) -> None:
    result = subprocess.run(
        [
            str(_target_python()),
            "-c",
            "import importlib.metadata; print(importlib.metadata.version('responseiq'))",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    actual = result.stdout.strip()
    if actual != expected:
        raise RuntimeError(f"Package version mismatch: expected {expected}, got {actual}")
    print(f"Verified {PACKAGE_NAME}=={actual}")


def _run_api_health(port: int) -> None:
    process = subprocess.Popen(
        [str(_target_python()), "-m", "uvicorn", "responseiq.app:app", "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for _ in range(30):
            if process.poll() is not None:
                details = process.stderr.read() if process.stderr else ""
                raise RuntimeError(f"API process exited before health check: {details}")
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
                    if response.status == 200:
                        return
            except (OSError, URLError):
                time.sleep(1)
        raise RuntimeError("API health check timed out")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def verify_release(source: str, version: str, *, dist_dir: Path, api_port: int) -> None:
    _create_environment()
    if source == "local":
        _install_local(version, dist_dir)
    elif source == "pypi":
        _install_pypi(version)
    else:
        raise ValueError(f"Unsupported verification source: {source}")

    _run([str(_target_python()), "-m", "responseiq.cli", "--help"])
    _verify_installed_version(version)
    _run_api_health(api_port)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("local", "pypi"), required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--dist-dir", type=Path, default=Path("dist"))
    parser.add_argument("--api-port", type=int, required=True)
    args = parser.parse_args()
    verify_release(args.source, args.version.removeprefix("v"), dist_dir=args.dist_dir, api_port=args.api_port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
