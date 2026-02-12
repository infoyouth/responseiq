import glob
import logging
import os
from typing import Dict

from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from ..schemas.blueprint import Blueprint

_REGISTRY: Dict[str, Blueprint] = {}
_YAML = YAML(typ="safe")


def _load_file(path: str) -> Blueprint:
    with open(path, "r", encoding="utf-8") as fh:
        data = _YAML.load(fh)
    # Pydantic v2 method
    bp = Blueprint.model_validate(data)
    return bp


def reload_blueprints():
    """Reload all blueprints from the package directory into memory."""
    global _REGISTRY
    base_dir = os.path.dirname(__file__)
    patterns = [
        os.path.join(base_dir, "*.yml"),
        os.path.join(base_dir, "*.yaml"),
        os.path.join(base_dir, "*.json"),
    ]
    registry: Dict[str, Blueprint] = {}
    for pat in patterns:
        for path in glob.glob(pat):
            try:
                bp = _load_file(path)
            except (YAMLError, ValidationError) as exc:
                # skip invalid blueprint files but continue loading others
                logging.warning("skipping invalid blueprint %s: %s", path, exc)
                continue
            # last-wins if duplicate ids
            registry[bp.id] = bp
    _REGISTRY = registry


def get_all():
    return list(_REGISTRY.values())


def get(blueprint_id: str) -> Blueprint | None:
    return _REGISTRY.get(blueprint_id)


# load at import time
reload_blueprints()
