from fastapi import APIRouter, HTTPException
from typing import List

from ..schemas.blueprint import Blueprint
from ..blueprints import get_all, get

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
