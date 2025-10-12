from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class Log(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: str | None = None


class Incident(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    log_id: int
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: str | None = None
    description: str | None = None
