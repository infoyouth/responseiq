from fastapi.testclient import TestClient

from responseiq.app import app

client = TestClient(app)


def test_openapi_contains_schemas():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    schemas = spec.get("components", {}).get("schemas", {})
    # Ensure our schemas are present
    assert "LogIn" in schemas
    assert "LogOut" in schemas
    assert "IncidentOut" in schemas
