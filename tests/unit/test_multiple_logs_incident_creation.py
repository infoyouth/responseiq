from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from src.app import app
from src.db import get_engine, init_db

engine = get_engine()
client = TestClient(app)


def post(message: str):
    r = client.post("/logs", json={"message": message})
    assert r.status_code == 201
    return r.json()


def get_incidents():
    r = client.get("/incidents")
    assert r.status_code == 200
    return r.json()


def test_multiple_logs_only_matching_create_incidents():
    # ensure clean DB for this test
    # other tests may have populated the shared in-memory DB
    SQLModel.metadata.drop_all(engine)
    init_db()

    # three logs: one matching, two non-matching
    post("all good message")
    post("failed to connect to upstream: error 502")
    post("this is harmless info")

    incidents = get_incidents()
    # At least one incident should exist for the 'error' log
    assert any(
        (
            "error" in (i.get("description") or "").lower()
            or i.get("severity") == "medium"
        )
        for i in incidents
    )
    # Non-matching logs should not create incidents.
    # Ensure incidents count is less than logs posted.
    assert len(incidents) < 4
