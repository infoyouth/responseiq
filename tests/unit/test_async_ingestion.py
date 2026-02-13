import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from responseiq.app import app
from responseiq.config.settings import settings
from responseiq.db import get_engine
from responseiq.models import Incident, Log


@pytest.fixture(name="client")
def client_fixture():
    # Force in-memory DB for this test module to ensure StaticPool usage
    # This is crucial for sharing DB state between main thread and background tasks
    settings.database_url = "sqlite:///:memory:"

    # Reset engine to force recreation with new settings
    import responseiq.db

    responseiq.db._engine = None

    # Use context manager to trigger lifespan events (init_db)
    with TestClient(app) as client:
        yield client

    # Cleanup
    responseiq.db._engine = None


def test_async_ingestion_creates_incident(client):
    """
    Verify that posting a log triggers the background task
    and eventually creates an incident in the DB.
    """
    # 1. Post a log that should trigger an incident (OOMKilled is 'high' severity)
    payload = {
        "message": "System detected OOMKilled process",
        "severity": "info",  # Intentionally mismatching to see if analyzer updates it
    }

    resp = client.post("/logs", json=payload)

    # 2. Verify immediate response
    assert resp.status_code == 202
    data = resp.json()
    assert data["message"] == payload["message"]
    log_id = data["id"]

    # 3. Verify Background Task Execution
    # TestClient runs background tasks synchronously before returning.
    # So we can check the DB immediately.

    engine = get_engine()
    with Session(engine) as session:
        # Check Log was updated
        log = session.get(Log, log_id)
        assert log is not None
        # The analyzer maps 'OOMKilled' -> 'high' severity
        # Our background task should have updated the log record
        assert log.severity == "high"

        # Check Incident was created
        statement = select(Incident).where(Incident.log_id == log_id)
        incident = session.exec(statement).first()
        assert incident is not None
        # With AI analysis, check that memory/OOM issue was detected properly
        # Either the exact keyword or AI-analyzed memory issue description
        assert (
            "OOMKilled" in incident.description
            or "Memory" in incident.description
            or "Resource Exhaustion" in incident.description
        )
        assert incident.severity == "high"


def test_async_ingestion_no_incident(client):
    """Verify standard logs are ingested but create no incident."""
    payload = {"message": "Just a normal log message"}
    resp = client.post("/logs", json=payload)
    assert resp.status_code == 202

    log_id = resp.json()["id"]

    engine = get_engine()
    with Session(engine) as session:
        # Incident should NOT exist
        statement = select(Incident).where(Incident.log_id == log_id)
        incident = session.exec(statement).first()
        assert incident is None
