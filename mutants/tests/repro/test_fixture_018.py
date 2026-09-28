import pytest
@pytest.fixture
def buggy_code():
    return "unknown_error"

def test_bug(buggy_code):
    assert buggy_code == "unknown_error"
    raise AssertionError("Expected unknown error, got something else")