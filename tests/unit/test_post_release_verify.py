import io
import importlib.util
import json
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "post_release_verify.py"
_SPEC = importlib.util.spec_from_file_location("post_release_verify", _SCRIPT_PATH)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
_pypi_wheel_url = _MODULE._pypi_wheel_url
_resolve_pypi_wheel = _MODULE._resolve_pypi_wheel
TEST_VERSION = "0.0.0"


class JsonResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_pypi_wheel_url_selects_universal_wheel():
    payload = {
        "urls": [
            {"filename": f"responseiq-{TEST_VERSION}.tar.gz", "url": "sdist"},
            {"filename": f"responseiq-{TEST_VERSION}-py3-none-any.whl", "url": "wheel"},
        ]
    }

    assert (
        _pypi_wheel_url(
            TEST_VERSION,
            opener=lambda request, timeout: JsonResponse(json.dumps(payload).encode()),
        )
        == "wheel"
    )


def test_resolve_pypi_wheel_retries_metadata_failures():
    attempts = 0
    sleeps = []

    def opener(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise OSError("not propagated yet")
        payload = {"urls": [{"filename": f"responseiq-{TEST_VERSION}-py3-none-any.whl", "url": "wheel"}]}
        return JsonResponse(json.dumps(payload).encode())

    assert _resolve_pypi_wheel(TEST_VERSION, retries=3, delay_seconds=0, opener=opener, sleep=sleeps.append) == "wheel"
    assert attempts == 3
    assert sleeps == [0, 0]


def test_resolve_pypi_wheel_fails_after_retries():
    with pytest.raises(RuntimeError, match="Unable to resolve"):
        _resolve_pypi_wheel(
            TEST_VERSION,
            retries=2,
            delay_seconds=0,
            opener=lambda request, timeout: (_ for _ in ()).throw(OSError("unavailable")),
            sleep=lambda _: None,
        )
