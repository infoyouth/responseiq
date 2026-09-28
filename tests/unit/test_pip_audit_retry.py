import subprocess
import importlib.util
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "pip_audit_retry.py"
_SPEC = importlib.util.spec_from_file_location("pip_audit_retry", _SCRIPT_PATH)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
run_audit = _MODULE.run_audit


def _result(returncode: int, output: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["pip-audit"], returncode=returncode, stdout=output, stderr="")


def test_retries_transient_service_failure_then_succeeds(tmp_path: Path):
    results = iter(
        [
            _result(1, "503 Server Error: Backend is unhealthy"),
            _result(0, "No known vulnerabilities found"),
        ]
    )
    sleeps: list[float] = []

    assert (
        run_audit(
            tmp_path / "audit.json",
            retries=2,
            delay_seconds=0,
            runner=lambda *args, **kwargs: next(results),
            sleep=sleeps.append,
        )
        == 0
    )
    assert sleeps == [0]


def test_does_not_retry_non_transient_audit_failure(tmp_path: Path):
    calls = 0

    def runner(*args, **kwargs):
        nonlocal calls
        calls += 1
        return _result(1, "Found 1 known vulnerability")

    assert run_audit(tmp_path / "audit.json", retries=3, delay_seconds=0, runner=runner, sleep=lambda _: None) == 1
    assert calls == 1
