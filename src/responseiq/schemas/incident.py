from typing import Any, Optional

from pydantic import BaseModel


class IncidentOut(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = "unknown"
    impact_score: Optional[float] = None
    impact_factors: Optional[dict[str, Any]] = None
