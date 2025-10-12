import os

# ensure test DB isolation
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


def test_duplicate_logs_are_stored():
    payload = {"message": "critical: panic when allocating resource"}
    r1 = client.post("/logs", json=payload)
    r2 = client.post("/logs", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201
    b1 = r1.json()
    b2 = r2.json()
    # Stored as separate rows (IDs different)
    assert b1.get("id") != b2.get("id")

    # Both should have created incidents
    resp = client.get("/incidents")
    assert resp.status_code == 200
    incidents = resp.json()
    # Expect at least two incidents matching panic/critical
    panic_incidents = [i for i in incidents if (i.get("title") or "").lower().find("panic") >= 0 or i.get("severity") == "high"]
    assert len(panic_incidents) >= 2
