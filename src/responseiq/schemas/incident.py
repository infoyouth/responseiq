from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel


class IncidentSeverity(Enum):
    """Incident severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LogEntry(BaseModel):
    """Individual log entry."""

    timestamp: datetime
    level: str
    service: str
    message: str
    metadata: Optional[dict] = None


class Incident(BaseModel):
    """Core incident representation for analysis."""

    id: str
    title: str
    description: str
    severity: IncidentSeverity
    service: str
    logs: List[LogEntry]
    tags: List[str]
    created_at: datetime
    resolved_at: Optional[datetime] = None
    source_repo: Optional[str] = None
    metadata: Optional[dict] = None


class IncidentOut(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = "unknown"
    impact_score: Optional[float] = None
    impact_factors: Optional[dict[str, Any]] = None
