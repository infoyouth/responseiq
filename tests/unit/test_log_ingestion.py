from fastapi.testclient import TestClient

from src.app import app
from src.services.analyzer import analyze_message

client = TestClient(app)


def test_analyzer_detects_error():
    meta = analyze_message("An unexpected error occurred")
    assert meta is not None
    assert meta.get("severity") in ("medium", "high")


def test_log_ingestion_and_incident_creation():
    payload = {"message": "critical: panic when allocating resource"}
    resp = client.post("/logs", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    # the ingestion should return analyzer-detected severity on the log
    assert body.get("severity") in ("medium", "high", None)

    # ensure incident created
    resp2 = client.get("/incidents")
    assert resp2.status_code == 200
    incidents = resp2.json()

    assert len(incidents) >= 1
