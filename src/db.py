import os

from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

# Reuse models from src.models to avoid duplicate table definitions
from .models import Log, Incident  # noqa: F401


_engine = None


def get_engine():
    """Lazily create and return the SQLAlchemy engine based on env var.

    This allows tests to set DATABASE_URL before the engine is constructed.
    """
    global _engine
    if _engine is not None:
        return _engine

    database_url = os.getenv("DATABASE_URL", "sqlite:///./responseiq.db")
    # Configure engine to support in-memory sqlite for tests (thread-safe)
    if database_url == "sqlite:///:memory:":
        _engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    else:
        _engine = create_engine(database_url, echo=False)

    return _engine


def init_db():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session


# Note: do NOT create a module-level engine here; call `get_engine()` when needed.
