from fastapi.testclient import TestClient

from responseiq.app import app

client = TestClient(app)


def test_missing_message_returns_422():
    resp = client.post("/logs", json={})
    assert resp.status_code == 422


def test_empty_message_returns_422():
    resp = client.post("/logs", json={"message": ""})
    # Pydantic will accept empty string unless we enforce stricter validation.
    # We expect a 422 here; tests will be adjusted if behavior differs.
    assert resp.status_code == 422
