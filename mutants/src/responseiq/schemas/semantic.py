# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Response schema for semantic incident similarity.

Returned by ``GET /api/v1/incidents/{id}/similar``. Each entry carries
a cosine similarity score against stored text-embedding vectors;
scores at or above 0.92 are considered duplicate-class incidents.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SimilarIncidentOut(BaseModel):
    incident_id: int = Field(description="ID of the similar Incident row.")
    log_id: int = Field(description="ID of the source Log row.")
    similarity_score: float = Field(description="Cosine similarity [0.0 – 1.0]. ≥ 0.92 considered duplicate-class.")
    description: Optional[str] = Field(default=None, description="Incident description.")
    severity: Optional[str] = None
    model: str = Field(description="Embedding model used for this comparison.")


class SimilaritySearchResult(BaseModel):
    query_incident_id: int
    threshold: float
    results: List[SimilarIncidentOut]
    source: str = Field(
        default="semantic_cache",
        description="'semantic_cache' when result is served from embedding store.",
    )
