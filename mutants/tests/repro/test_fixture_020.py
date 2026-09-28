import pytest

@pytest.fixture
def buggy_code():
    return "return 'UnknownError: Incident reproduction required'
"