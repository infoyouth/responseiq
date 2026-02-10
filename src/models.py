from datetime import datetime, timezone

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
    source: str | None = Field(
        default="unknown", description="detection source: ai or rules"
    )
