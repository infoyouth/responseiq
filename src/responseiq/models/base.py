from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _now():
    return datetime.now(timezone.utc)


class Log(SQLModel, table=True):  # type: ignore[call-arg]
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    message: str
    timestamp: datetime = Field(default_factory=_now)
    severity: str | None = None


class Incident(SQLModel, table=True):  # type: ignore[call-arg]
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    log_id: int
    detected_at: datetime = Field(default_factory=_now)
    severity: str | None = None
    description: str | None = None
    source: str | None = Field(default="unknown", description="detection source: ai or rules")


class FeedbackRecord(SQLModel, table=True):  # type: ignore[call-arg]
    """P-F1: Human approval/rejection of a suggested remediation."""

    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    log_id: int = Field(index=True)
    approved: bool
    comment: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_now)


class IncidentEmbedding(SQLModel, table=True):  # type: ignore[call-arg]
    """P-F2: Text embedding for semantic incident deduplication.

    ``embedding_json`` stores a JSON-encoded list[float] (1536 dims for
    text-embedding-3-small).  This is SQLite + Postgres compatible today.
    A pgvector VECTOR(1536) column can replace it in future without changing
    the service layer.
    """

    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    incident_id: int = Field(index=True, unique=True)
    log_id: int = Field(index=True)
    embedding_json: str = Field(description="JSON-encoded float array.")
    model: str = Field(default="text-embedding-3-small")
    created_at: datetime = Field(default_factory=_now)
