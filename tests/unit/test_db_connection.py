import os

from sqlmodel import create_engine

def test_sqlite_memory_engine():
    url = "sqlite:///:memory:"
    engine = create_engine(url)
    assert engine is not None
import os

# Ensure tests use in-memory sqlite to avoid Docker
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from src.db import init_db, get_engine
engine = get_engine()
from sqlmodel import SQLModel


def test_init_db_creates_tables():
    # Should not raise
    init_db()
    # Check that tables are present in metadata
    assert SQLModel.metadata.tables, "No tables found after init_db()"
