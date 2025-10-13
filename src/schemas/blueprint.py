from typing import List, Optional
from pydantic import BaseModel, Field, condecimal, confloat


class Action(BaseModel):
    type: str
    target: Optional[str] = None
    patch: Optional[str] = None


class RollbackStep(BaseModel):
    type: str
    target: Optional[str] = None
    command: Optional[str] = None


class Blueprint(BaseModel):
    id: str
    title: str
    incident_signature: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    rationale: Optional[str] = None
    confidence: Optional[float] = Field(default=0.0)
    blast_radius: Optional[str] = None
    actions: List[Action] = Field(default_factory=list)
    rollback: List[RollbackStep] = Field(default_factory=list)
    examples: List[dict] = Field(default_factory=list)
