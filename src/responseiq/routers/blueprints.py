# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Blueprint CRUD router.

Exposes ``GET /blueprints/`` and ``GET /blueprints/{id}`` endpoints
that serve remediation blueprints loaded from the in-memory registry.
"""

from typing import List

from fastapi import APIRouter, Header, HTTPException

from ..blueprints import get, get_all
from ..config.settings import settings
from ..schemas.blueprint import Blueprint

router = APIRouter(prefix="/blueprints", tags=["blueprints"])


@router.get("/", response_model=List[Blueprint])
def list_blueprints():
    return get_all()


@router.get("/{blueprint_id}", response_model=Blueprint)
def get_blueprint(blueprint_id: str):
    bp = get(blueprint_id)
    if not bp:
        raise HTTPException(status_code=404, detail="blueprint not found")
    return bp


@router.post("/reload", summary="Reload blueprints from disk")
def reload_blueprints_admin(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    # Protect reload with a simple token set in env BLUEPRINT_RELOAD_TOKEN
    required = settings.blueprint_reload_token
    if required and x_admin_token != required:
        raise HTTPException(status_code=401, detail="unauthorized")
    # perform reload
    from ..blueprints import reload_blueprints

    reload_blueprints()
    return {"reloaded": True}
