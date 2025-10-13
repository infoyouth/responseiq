from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


def test_list_blueprints():
    resp = client.get("/blueprints/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(bp["id"] == "crashloop_increase_memory" for bp in data)


def test_get_blueprint_detail():
    resp = client.get("/blueprints/crashloop_increase_memory")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "crashloop_increase_memory"
