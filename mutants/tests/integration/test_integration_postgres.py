import os
import subprocess
import time

import requests

# Integration tests are only run when RUN_INTEGRATION=1 in the environment
RUN = os.environ.get("RUN_INTEGRATION") == "1"


def wait_for(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def test_postgres_integration():
    if not RUN:
        import pytest

        msg = "Integration tests disabled; set RUN_INTEGRATION=1 to enable"
        pytest.skip(msg)

    # bring up docker-compose stack
    subprocess.check_call(["docker", "compose", "up", "-d", "--build"])

    try:
        # wait for app to be ready
        ready = wait_for("http://localhost:8000/health") or wait_for("http://localhost:8000/docs")
        if not ready:
            print("App failed to start. Logs:")
            subprocess.call(["docker", "compose", "logs", "app"])
        assert ready, "app did not start"

        # Post a log
        resp = requests.post(
            "http://localhost:8000/logs",
            json={"message": "integration test critical panic"},
        )
        if resp.status_code != 202:
            print(f"POST /logs error: {resp.text}")
        assert resp.status_code == 202
        body = resp.json()
        assert "id" in body

        # Poll for incidents
        # Give a moment for background task
        time.sleep(2)
        resp_inc = requests.get("http://localhost:8000/incidents")
        if resp_inc.status_code != 200:
            print(f"GET /incidents error: {resp_inc.text}")

        assert resp_inc.status_code == 200
        incidents = resp_inc.json()

        assert any((i.get("severity") == "high" or "panic" in (i.get("description") or "")) for i in incidents)
    except Exception:
        subprocess.call(["docker", "compose", "logs", "app"])
        subprocess.call(["docker", "compose", "logs", "db"])
        raise
    finally:
        subprocess.check_call(["docker", "compose", "down", "-v"])
