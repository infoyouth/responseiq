This folder contains sample log fixtures and a small harness to run "reality" checks against the ResponseIQ MVP.

Structure:
- `fixtures/` contains JSON files with `message` and optional `expected_incident_severity`.
- `tests/fixtures/test_fixtures_harness.py` posts each fixture to `POST /logs` using FastAPI TestClient and asserts whether an incident was created with the expected severity.

Run locally:

1. From the repo root run the unit tests (the harness uses an in-memory SQLite DB):

   `pytest tests/fixtures/test_fixtures_harness.py -q`

2. To run the full test suite including the harness:

   `pytest -q`

Notes:
- The harness reads fixture JSON files under this folder. Add more fixtures to expand coverage.
