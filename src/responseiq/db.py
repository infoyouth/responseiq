from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from .config.settings import settings

# Reuse models from responseiq.models to avoid duplicate table definitions
from .models import Incident, Log  # noqa: F401

_engine = None


def get_engine():
    """Lazily create and return the SQLAlchemy engine based on env var.

    This allows tests to set DATABASE_URL before the engine is constructed.
    """
    global _engine
    if _engine is not None:
        return _engine

    database_url = settings.database_url
    # Configure engine to support in-memory sqlite for tests (thread-safe)
    if database_url == "sqlite:///:memory:":
        _engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    else:
        _engine = create_engine(
            database_url,
            echo=False,
        )

    return _engine


def init_db():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session


# Note: avoid creating a module-level engine here.
# Use `get_engine()` when an engine is required so tests can set DATABASE_URL.
