import os

# Use an in-memory SQLite DB for unit tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from src.db import get_session, init_db


def test_db_init():
    init_db()
    s = get_session()
    assert s is not None
