"""src/responseiq/plugins/nodejs_parser.py

P5.2 built-in parser: Node.js / Express error logs.

Detects and extracts structured context from Node.js/Express logs:
  - V8/Node.js Error: ... + at ... stack traces
  - Express/Connect error middleware output
  - Unhandled promise rejections
  - JSON-structured logs (Bunyan / Pino / Winston)
  - npm module errors (MODULE_NOT_FOUND, etc.)
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from responseiq.plugins.base import BasePlugin, PluginMetadata

# ── signatures ───────────────────────────────────────────────────────────────
_NODE_SIGNALS: List[str] = [
    "at Object.<anonymous>",
    "at Module._compile",
    "UnhandledPromiseRejection",
    "UnhandledPromiseRejectionWarning",
    "MODULE_NOT_FOUND",
    "process.on('uncaughtException'",
    "express",
    "node_modules",
    "ReferenceError:",
    "TypeError: Cannot",
]

# ── patterns ─────────────────────────────────────────────────────────────────
_ERROR_MSG_RE = re.compile(r"^(?P<type>\w+Error|Error):\s+(?P<msg>.+)$", re.MULTILINE)
_AT_FRAME_RE = re.compile(
    r"\s+at\s+(?:(?P<func>[\w.<>$\s]+?)\s+)?\((?P<file>[^)]+\.(?:js|ts|mjs|cjs)):(?P<line>\d+):(?P<col>\d+)\)"
)
_PROMISE_RE = re.compile(
    r"UnhandledPromiseRejection(?:Warning)?:?\s*(?:reason:\s*)?(?P<reason>.+)",
    re.IGNORECASE,
)
_EXPRESS_STATUS_RE = re.compile(r"(?P<method>GET|POST|PUT|DELETE|PATCH)\s+(?P<path>/\S+)\s+(?P<status>[45]\d{2})")


def _try_parse_json_log(line: str) -> Optional[Dict[str, Any]]:
    """Attempt to parse a Pino/Bunyan/Winston JSON log line."""
    try:
        data = json.loads(line)
        if isinstance(data, dict) and ("level" in data or "msg" in data or "message" in data):
            return data
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _extract_json_errors(log_text: str) -> List[Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    for line in log_text.splitlines():
        parsed = _try_parse_json_log(line.strip())
        if parsed:
            level = str(parsed.get("level", "")).lower()
            if level in ("error", "fatal", "50", "60"):
                errors.append(parsed)
    return errors


def _extract_stack_frames(log_text: str) -> List[Dict[str, str]]:
    return [
        {
            "function": (m.group("func") or "").strip() or "<anonymous>",
            "file": m.group("file"),
            "line": m.group("line"),
            "column": m.group("col"),
        }
        for m in _AT_FRAME_RE.finditer(log_text)
    ]


def _extract_error_types(log_text: str) -> List[Dict[str, str]]:
    seen: set[str] = set()
    results: List[Dict[str, str]] = []
    for m in _ERROR_MSG_RE.finditer(log_text):
        key = m.group("type") + m.group("msg")[:40]
        if key not in seen:
            seen.add(key)
            results.append({"type": m.group("type"), "message": m.group("msg").strip()})
    return results


class NodejsParser(BasePlugin):
    """Parses Node.js / Express error logs and enriches the agent state."""

    metadata = PluginMetadata(
        name="nodejs_parser",
        version="1.0.0",
        author="responseiq-core",
        log_format="Node.js/Express",
        description=(
            "Extracts V8 stack traces, unhandled promise rejections, "
            "Express HTTP errors, and JSON structured log errors from Node.js logs."
        ),
    )

    @classmethod
    def can_handle(cls, log_text: str) -> bool:
        return any(sig in log_text for sig in _NODE_SIGNALS)

    def run(self, agent_state: dict) -> dict:
        messages: List[str] = agent_state.get("messages", [])
        combined = "\n".join(str(m) for m in messages)

        frames = _extract_stack_frames(combined)
        error_types = _extract_error_types(combined)
        json_errors = _extract_json_errors(combined)

        promise_match = _PROMISE_RE.search(combined)
        express_errors = [
            {"method": m.group("method"), "path": m.group("path"), "status": int(m.group("status"))}
            for m in _EXPRESS_STATUS_RE.finditer(combined)
        ]

        parsed: Dict[str, Any] = {
            "framework": "nodejs",
            "error_types": error_types,
            "stack_frames": frames[:20],
            "top_frame": frames[0] if frames else None,
            "express_errors": express_errors,
            "json_log_errors": json_errors[:5],
            "unhandled_promise": promise_match.group("reason").strip() if promise_match else None,
        }
        return {"parsed_context": parsed}
