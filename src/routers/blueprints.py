from fastapi import APIRouter, HTTPException, Header
from typing import List

from ..schemas.blueprint import Blueprint
from ..blueprints import get_all, get
import os



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
    required = os.environ.get("BLUEPRINT_RELOAD_TOKEN")
    if required and x_admin_token != required:
        raise HTTPException(status_code=401, detail="unauthorized")
    # perform reload
    from ..blueprints import reload_blueprints

    reload_blueprints()
    return {"reloaded": True}
