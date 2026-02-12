from typing import Optional

from pydantic import BaseModel, Field


class LogIn(BaseModel):
    # enforce non-empty messages
    message: str = Field(..., min_length=1)
    severity: Optional[str] = None


class LogOut(BaseModel):
    id: Optional[int]
    message: str
    severity: Optional[str] = None
