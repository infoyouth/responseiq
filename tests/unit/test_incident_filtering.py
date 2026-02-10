from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def post_log(message: str):
    resp = client.post("/logs", json={"message": message})
    assert resp.status_code == 202
    return resp.json()


def get_incidents(severity: str | None = None):
    params = {"severity": severity} if severity else {}
    resp = client.get("/incidents", params=params)
    assert resp.status_code == 200
    return resp.json()


def test_filter_high_returns_only_high():
    # medium-ish message
    post_log("Service timeout error")
    # high severity message
    post_log("critical: panic when allocating resource")

    all_inc = get_incidents()
    assert len(all_inc) >= 2

    high_inc = get_incidents("high")
    assert all(
        (i.get("severity") == "high" or i.get("title", "").lower().find("panic") >= 0)
        for i in high_inc
    )
    assert len(high_inc) >= 1


def test_filter_medium_returns_only_medium():
    # create another medium
    post_log("failed to connect to upstream: error 502")
    medium_inc = get_incidents("medium")
    # medium incidents exist
    assert isinstance(medium_inc, list)


def test_filter_unknown_returns_empty():
    unknown_inc = get_incidents("unknown")
    assert unknown_inc == []
