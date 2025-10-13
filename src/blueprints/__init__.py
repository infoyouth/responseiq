"""Blueprints package: stores remediation blueprints used by the MVP.

Loader provides a simple in-memory registry of blueprints loaded from
YAML/JSON files under `src/blueprints/`.
"""

from .loader import get_all, get

__all__ = ["get_all", "get"]
