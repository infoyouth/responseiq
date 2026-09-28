import pytest

@pytest.fixture
def mock_network():
    return {'status': 'success'}

def test_bug_4672ae5b_d13b_45e3_9102_6bd42d339b6d(mock_network):
    assert mock_network['status'] == 'success'
    with pytest.raises(UnknownError) as e:
        # Simulate an external dependency failure
        return mock_network['status']
    assert str(e.value) == 'Incident reproduction required'