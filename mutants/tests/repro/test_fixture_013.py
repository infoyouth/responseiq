import pytest
@pytest.fixture
def buggy_code():
    return 1 / 0
def test_buggy_code(buggy_code):
    assert buggy_code == 1/0
pytest.raises(ZeroDivisionError, test_buggy_code)