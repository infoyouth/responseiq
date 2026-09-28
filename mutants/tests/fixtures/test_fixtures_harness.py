import glob
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from responseiq.app import app
from responseiq.db import init_db


@pytest.fixture(autouse=True)
def setup_db():
    # ensure DB is initialized for each test run (in-memory)
    init_db()
    yield


def load_fixtures():
    base = Path(__file__).resolve().parents[2] / "fixtures"
    files = sorted(glob.glob(str(base / "*.json")))
    fixtures = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            fixtures.append(json.load(fh))
    return fixtures


def test_fixtures_create_expected_incidents():
    # tests should use an in-memory sqlite DB for isolation
    import os

    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    from sqlmodel import SQLModel

    from responseiq.db import get_engine, init_db

    client = TestClient(app)
    fixtures = load_fixtures()

    for fx in fixtures:
        # reset DB to ensure fixture isolation
        SQLModel.metadata.drop_all(get_engine())
        init_db()
        payload = {"message": fx["message"]}

        # Ingest Log
        resp = client.post("/logs", json=payload)
        assert resp.status_code == 202

        # Check Incidents
        # Background task should have finished, so DB is updated.
        inc_resp = client.get("/incidents")
        assert inc_resp.status_code == 200
        incidents = inc_resp.json()

        expected_sev = fx.get("expected_incident_severity")

        if expected_sev is None:
            # expect NO incidents created for this log
            # (or at least none matching severity?)
            # The original test logic seemed to imply we check incidents.
            # If expected is None, we expect empty list or list of unrelated?
            # Since we drop_all() every loop, list should be empty.
            assert len(incidents) == 0, f"Expected no incidents, found {incidents}"
        else:
            # expect at least one incident with the expected severity
            found = any(i.get("severity") == expected_sev for i in incidents)
            assert found, f"Expected severity {expected_sev} in incidents: {incidents}"
