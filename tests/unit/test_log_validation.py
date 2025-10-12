import os

# ensure test DB isolation
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


def test_missing_message_returns_422():
    resp = client.post("/logs", json={})
    assert resp.status_code == 422


def test_empty_message_returns_422():
    resp = client.post("/logs", json={"message": ""})
    # Pydantic will accept empty string unless we enforce; current behavior may be 201 or 422
    # Assert 422 to capture desired stricter validation; if behavior is different we'll adapt.
    assert resp.status_code == 422
