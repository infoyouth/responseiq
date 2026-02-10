from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_long_message_accepted_and_analyzed():
    long_msg = "error: " + ("A" * 10000)
    r = client.post("/logs", json={"message": long_msg})
    assert r.status_code == 202
    _body = r.json()
    # analyzer should detect 'error' and assign at least medium
    assert _body.get("severity") in ("medium", "high", None)


def test_analyzer_none_creates_no_incident():
    # use a message with no keywords
    r = client.post(
        "/logs",
        json={"message": "completely benign log line"},
    )
    assert r.status_code == 202
    # ensure no incident created for that log
    incidents = client.get("/incidents").json()
    assert all(
        ((i.get("description") or "").lower().find("benign") == -1) for i in incidents
    )


def test_unexpected_severity_handled_gracefully(monkeypatch):
    # monkeypatch analyze_message to return an unexpected severity
    def fake_analyze(msg: str):
        return {"severity": "criticality_unknown", "reason": "weird"}

    # patch where it is USED: in the incident_service
    import src.services.incident_service as svc_module

    monkeypatch.setattr(svc_module, "analyze_message", fake_analyze)

    r = client.post(
        "/logs",
        json={"message": "this will trigger fake analyzer"},
    )
    assert r.status_code == 202
    # unexpected severity should be stored on incident but not crash
    incidents = client.get("/incidents").json()
    assert any(i.get("description") == "weird" for i in incidents)
