import os
import glob
import yaml
from typing import Dict, Any

from ..schemas.blueprint import Blueprint

_REGISTRY: Dict[str, Blueprint] = {}


def _load_file(path: str) -> Blueprint:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    bp = Blueprint.parse_obj(data)
    return bp


def reload_blueprints():
    """Reload all blueprints from the package directory into memory."""
    global _REGISTRY
    base_dir = os.path.dirname(__file__)
    patterns = [os.path.join(base_dir, "*.yml"), os.path.join(base_dir, "*.yaml"), os.path.join(base_dir, "*.json")]
    registry: Dict[str, Blueprint] = {}
    for pat in patterns:
        for path in glob.glob(pat):
            try:
                bp = _load_file(path)
            except Exception:
                # skip invalid blueprint files but continue loading others
                continue
            if bp.id in registry:
                # last-wins if duplicate ids
                pass
            registry[bp.id] = bp
    _REGISTRY = registry


def get_all():
    return list(_REGISTRY.values())


def get(blueprint_id: str) -> Blueprint | None:
    return _REGISTRY.get(blueprint_id)


# load at import time
reload_blueprints()
