from sqlmodel import SQLModel, create_engine

from src.db import get_engine, init_db


def test_sqlite_memory_engine():
    url = "sqlite:///:memory:"
    engine = create_engine(url)
    assert engine is not None


engine = get_engine()


def test_init_db_creates_tables():
    # Should not raise
    init_db()
    # Check that tables are present in metadata
    assert SQLModel.metadata.tables, "No tables found after init_db()"
