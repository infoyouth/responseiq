from typing import List, Optional
from pydantic import BaseModel, Field, condecimal, confloat


class Action(BaseModel):
    type: str
    target: Optional[str]
    patch: Optional[str]


class RollbackStep(BaseModel):
    type: str
    target: Optional[str]
    command: Optional[str]


class Blueprint(BaseModel):
    id: str
    title: str
    incident_signature: Optional[str]
    severity: Optional[str]
    description: Optional[str]
    rationale: Optional[str]
    confidence: Optional[float] = Field(default=0.0)
    blast_radius: Optional[str]
    actions: List[Action] = Field(default_factory=list)
    rollback: List[RollbackStep] = Field(default_factory=list)
    examples: List[dict] = Field(default_factory=list)
