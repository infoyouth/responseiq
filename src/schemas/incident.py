from typing import Optional
from pydantic import BaseModel


class IncidentOut(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
