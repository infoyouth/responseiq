from fastapi.testclient import TestClient

from responseiq.app import app

client = TestClient(app)


def test_blueprints_ui_served():
    resp = client.get("/ui/blueprints")
    assert resp.status_code == 200
    text = resp.text
    # The static HTML is served; TestClient does not execute JS, so the page itself
    # won't contain dynamic blueprint data. Verify the page is present, then call
    # the API to ensure the blueprint exists.
    assert "Blueprints" in text
    api = client.get("/blueprints/")
    assert api.status_code == 200
    data = api.json()
    assert any(bp["id"] == "crashloop_increase_memory" for bp in data)
