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


def test_reload_blueprints_requires_token(monkeypatch):
    # Ensure reload endpoint requires token when env var is set
    monkeypatch.setenv("BLUEPRINT_RELOAD_TOKEN", "secret-token")
    resp = client.post("/blueprints/reload")
    assert resp.status_code == 401


def test_reload_blueprints_with_token(monkeypatch):
    monkeypatch.setenv("BLUEPRINT_RELOAD_TOKEN", "secret-token")
    resp = client.post("/blueprints/reload", headers={"X-Admin-Token": "secret-token"})
    assert resp.status_code == 200
    assert resp.json().get("reloaded") is True
