import pytest
@pytest.fixture
def mock_network():
    return {'status': 'success'}

def buggy_function(mock_network):
    if not mock_network['status'] == 'success':
        raise UnknownError('Incident reproduction required')
    return 0

def test_buggy_function(buggy_function, mock_network):
    with pytest.raises(UnknownError) as e:
        buggy_function(mock_network)
    assert str(e.value) == 'Incident reproduction required'
    # This assertion will fail because the function does not raise this error when the network status is success
    assert 0 == buggy_function(mock_network)