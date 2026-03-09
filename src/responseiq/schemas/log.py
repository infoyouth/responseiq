# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Log ingestion request/response schemas.

``LogIn`` is the payload accepted by ``POST /api/v1/logs`` and the
webhook ingest endpoints. ``LogOut`` is the serialised DB row returned
after storage. Both fields have minimal validation by design — noise
filtering happens downstream in the analyzer.
"""

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
