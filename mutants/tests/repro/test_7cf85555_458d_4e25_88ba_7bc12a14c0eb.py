import pytest

@pytest.fixture
def mock_network():
    return {'status': 'success'}

def test_bug(mock_network):
    # Mock external dependencies
    network = mock_network
    # Simulate the error condition
    assert network['status'] == 'success', 'Network status should be success'
    raise UnknownError('Incident reproduction required')

# Run the test with pytest
pytest -v --cov=.
