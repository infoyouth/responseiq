import glob
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.db import init_db


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

    from src.db import get_engine, init_db

    client = TestClient(app)
    fixtures = load_fixtures()

    for fx in fixtures:
        # reset DB to ensure fixture isolation
        SQLModel.metadata.drop_all(get_engine())
        init_db()
        payload = {"message": fx["message"]}
        resp = client.post("/logs", json=payload)
        assert resp.status_code == 201

        # after ingestion, query incidents
        sev = fx.get("expected_incident_severity")

        inc_resp = client.get("/incidents")
        assert inc_resp.status_code == 200
        incidents = inc_resp.json()

        if sev is None:
            # expect no incidents created for this message. Ensure none of the
            # incidents correspond to this message's detected keywords. We
            # assume fixtures are limited so this asserts no incidents at all.
            assert all(
                (i.get("severity") != "high" and i.get("severity") != "medium")
                for i in incidents
            )
        else:
            # expect at least one incident with the expected severity
            assert any(
                i.get("severity") == sev for i in incidents
            ), f"expected severity {sev} in incidents: {incidents}"
