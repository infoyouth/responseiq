# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""FastAPI / Uvicorn log parser.

Detects and extracts structured context from FastAPI and Uvicorn error
output — access log lines, ``HTTPException`` details, ASGI application
errors, Starlette exception handlers, and Pydantic ``ValidationError``
payloads.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from responseiq.plugins.base import BasePlugin, PluginMetadata

# ── signatures ───────────────────────────────────────────────────────────────
_FASTAPI_SIGNALS: List[str] = [
    "uvicorn",
    "fastapi",
    "starlette",
    "ASGI",
    "HTTPException",
    "pydantic",
    "ValidationError",
    "RequestValidationError",
]

# ── patterns ─────────────────────────────────────────────────────────────────
_ACCESS_LOG_RE = re.compile(
    r'(?P<client>\d+\.\d+\.\d+\.\d+:\d+)\s+-\s+"(?P<method>\w+)\s+(?P<path>/\S*)\s+HTTP/[\d.]+"'
    r"\s+(?P<status>\d{3})",
)
_HTTP_EXC_RE = re.compile(
    r"HTTPException.*?status_code[=:\s]+(?P<status>\d{3}).*?detail[=:\s]+[\"'](?P<detail>[^\"']+)",
    re.IGNORECASE | re.DOTALL,
)
_VALIDATION_FIELD_RE = re.compile(r"'loc':\s*\[(?P<loc>[^\]]+)\].*?'msg':\s*'(?P<msg>[^']+)'", re.DOTALL)
_TRACEBACK_FILE_RE = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<func>\S+)')


def _extract_access_errors(log_text: str) -> List[Dict[str, Any]]:
    return [
        {
            "client": m.group("client"),
            "method": m.group("method"),
            "path": m.group("path"),
            "status_code": int(m.group("status")),
        }
        for m in _ACCESS_LOG_RE.finditer(log_text)
        if int(m.group("status")) >= 400
    ]


def _extract_http_exception(log_text: str) -> Optional[Dict[str, Any]]:
    match = _HTTP_EXC_RE.search(log_text)
    if match:
        return {"status_code": int(match.group("status")), "detail": match.group("detail")}
    return None


def _extract_validation_errors(log_text: str) -> List[Dict[str, str]]:
    return [{"field": m.group("loc"), "message": m.group("msg")} for m in _VALIDATION_FIELD_RE.finditer(log_text)]


class FastAPIParser(BasePlugin):
    """Parses FastAPI / Uvicorn error logs and enriches the agent state."""

    metadata = PluginMetadata(
        name="fastapi_parser",
        version="1.0.0",
        author="responseiq-core",
        log_format="FastAPI/Uvicorn",
        description="Extracts HTTP errors, HTTPException details, and Pydantic ValidationError fields from FastAPI logs.",
    )

    @classmethod
    def can_handle(cls, log_text: str) -> bool:
        return any(sig.lower() in log_text.lower() for sig in _FASTAPI_SIGNALS)

    def run(self, agent_state: dict) -> dict:
        messages: List[str] = agent_state.get("messages", [])
        combined = "\n".join(str(m) for m in messages)

        frames = [
            {"file": m.group("file"), "line": m.group("line"), "function": m.group("func")}
            for m in _TRACEBACK_FILE_RE.finditer(combined)
        ]

        parsed: Dict[str, Any] = {
            "framework": "fastapi",
            "access_errors": _extract_access_errors(combined),
            "validation_errors": _extract_validation_errors(combined),
            "traceback_frames": frames,
        }
        http_exc = _extract_http_exception(combined)
        if http_exc:
            parsed["http_exception"] = http_exc

        return {"parsed_context": parsed}
