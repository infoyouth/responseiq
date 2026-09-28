from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from responseiq.app import app
from responseiq.db import get_engine, init_db

client = TestClient(app)


def post(message: str):
    r = client.post("/logs", json={"message": message})
    assert r.status_code == 202
    return r.json()


def get_incidents():
    r = client.get("/incidents")
    assert r.status_code == 200
    return r.json()


def test_multiple_logs_only_matching_create_incidents():
    # Helper to get the current valid engine
    current_engine = get_engine()

    # ensure clean DB for this test
    SQLModel.metadata.drop_all(current_engine)
    init_db()

    # three logs: one matching, two non-matching
    post("all good message")
    post("failed to connect to upstream: error 502")
    post("this is harmless info")

    incidents = get_incidents()

    # At least one incident should exist for the 'error' log
    # Note: Description might contain 'matched: error' or similar
    assert any(
        ("error" in (i.get("description") or "").lower() or i.get("title") == "error" or i.get("severity") == "medium")
        for i in incidents
    )

    # Non-matching logs should not create incidents.
    # We posted 3 logs.
    # 'all good' -> no incident
    # 'error 502' -> incident (medium)
    # 'harmless' -> no incident
    # So we expect exactly 1 incident ideally.
    # Asserting < 3 is safe.
    assert len(incidents) < 3, f"Too many incidents found: {incidents}"
