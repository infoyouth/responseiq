import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# Add src to sys.path so we can import 'responseiq' directly
sys.path.insert(0, str(ROOT / "src"))

# Give every xdist worker its own SQLite file so connection pools never race.
# PYTEST_XDIST_WORKER is set to e.g. "gw0", "gw1" … by pytest-xdist;
# falls back to "master" for a plain (non-parallel) run which uses :memory:.
_xdist_worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
if _xdist_worker == "master":
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
else:
    # File-based per-worker DB — each xdist process is fully isolated.
    _db_path = f"/tmp/responseiq_test_{_xdist_worker}.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

# Ensure tests always use mock LLM, never a real external endpoint.
# This overrides any .env file that may point to Ollama/OpenAI,
# so tests are deterministic and work offline.
# Individual tests that need real LLM behaviour must patch settings explicitly.
os.environ["LLM_BASE_URL"] = ""
os.environ.pop("OPENAI_API_KEY", None)


@pytest.fixture(autouse=True)
def _reset_db_engine():
    """Reset the cached SQLAlchemy engine before every test.

    ``db._engine`` is a module-level singleton. If a test leaves a
    transaction in a dirty state (e.g. due to an uncaught exception inside
    a test or a FastAPI TestClient), the next test on the same worker
    inherits a broken connection and fails with SQLAlchemy e3q8.
    Resetting the global forces ``get_engine()`` to build a fresh engine
    (and therefore a fresh connection pool) for each test.
    """
    import responseiq.db as _db

    _db._engine = None
    # Re-create tables on the fresh engine so tests that use TestClient
    # (which calls init_db() only once at app startup) still find their tables.
    _db.init_db()
    yield
    _db._engine = None
