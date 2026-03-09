# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Database engine and session factory.

Builds a SQLAlchemy engine from ``settings.database_url`` (PostgreSQL via
psycopg3 in production, in-memory SQLite for tests) and exposes a
``get_session`` FastAPI dependency for use in routers.
"""

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from .config.settings import settings

# Reuse models from responseiq.models to avoid duplicate table definitions
from .models.base import FeedbackRecord, Incident, IncidentEmbedding, Log  # noqa: F401

_engine = None


def get_engine():
    """Lazily create and return the SQLAlchemy engine based on env var.

    This allows tests to set DATABASE_URL before the engine is constructed.
    """
    global _engine
    if _engine is not None:
        return _engine

    database_url = settings.database_url
    # Normalize PostgreSQL URL scheme for psycopg3.
    # psycopg3 (package: psycopg) uses the 'postgresql+psycopg' SQLAlchemy dialect.
    # Plain 'postgresql://' defaults to psycopg2 which is no longer a dependency.
    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgresql://") :]
    elif database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgres://") :]

    # Configure engine to support sqlite for tests (thread-safe).
    # Apply StaticPool + check_same_thread=False to ANY SQLite URL, including
    # per-worker file-based DBs used under pytest-xdist.
    if database_url.startswith("sqlite"):
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
