from typing import Optional, Dict, Any
import json
import os
from pathlib import Path

from src.schemas.incident import IncidentOut

# default in-package config path
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "keywords.json"

# runtime config
_config: Dict[str, Any] = {}


def reload_config(path: str | None = None) -> None:
    """Reload analyzer configuration from a JSON file.

    If `path` is None, loads from the default `src/config/keywords.json`.
    """
    global _config
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        # fallback to built-in defaults
        _config = {
            "simple": ["error", "exception", "failed", "panic", "critical"],
            "events": {"oomkilled": "OOMKilled", "crashloop": "CrashLoopBackOff", "502": "Nginx502"},
            "mapping": {"high": ["panic", "critical", "oomkilled", "crashloop"], "medium": ["error", "exception", "failed"]},
        }
        return

    with open(cfg_path, "r", encoding="utf-8") as fh:
        _config = json.load(fh)


# load configuration at import time
reload_config()


def analyze_message(message: str) -> Optional[dict]:
    """Simple keyword-based analyzer returning metadata for incidents.

    Returns a dict like {'severity': 'medium', 'reason': 'matched:error'} or None.
    """
    text = message.lower()
    for kw in _config.get("simple", []):
        if kw in text:
            # find severity by mapping
            mapping = _config.get("mapping", {})
            severity = None
            for sev, kws in mapping.items():
                if kw in kws:
                    severity = sev
                    break
            if severity is None:
                severity = "medium"
            return {"severity": severity, "reason": f"matched:{kw}"}
    return None


def analyze_log(log_text: str) -> Optional[IncidentOut]:
    """Event-oriented analyzer returning an IncidentOut for compatibility with older tests."""
    txt = log_text.lower()
    # event detection: return IncidentOut with both title and severity when applicable
    for k, title in _config.get("events", {}).items():
        if k in txt:
            # severity mapping may include events mapping
            mapping = _config.get("mapping", {})
            sev = None
            for s, kws in mapping.items():
                if k in kws:
                    sev = s
                    break
            if sev is None:
                sev = "high" if k in ("oomkilled", "crashloop") else "medium"
            return IncidentOut(id=None, title=title, severity=sev, description=f"Detected {title} from logs")
    return None

