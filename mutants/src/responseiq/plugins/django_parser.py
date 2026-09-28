# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Django log parser.

Detects and extracts structured context from Django error output —
ORM exceptions (``ObjectDoesNotExist``, ``MultipleObjectsReturned``),
4xx/5xx HTTP errors logged by ``django.request``, template errors, and
standard Python tracebacks emitted by Django's logging handlers.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from responseiq.plugins.base import BasePlugin, PluginMetadata

# ── signatures that identify a Django log ────────────────────────────────────
_DJANGO_SIGNALS: List[str] = [
    "django.request",
    "django.core.exceptions",
    "django.db.utils",
    "django.template",
    "ImproperlyConfigured",
    "ObjectDoesNotExist",
    "MultipleObjectsReturned",
    "django.core.handlers",
]

# ── patterns ─────────────────────────────────────────────────────────────────
_HTTP_ERROR_RE = re.compile(
    r'"(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(?P<path>/\S*)\s+HTTP/[\d.]+"'
    r"\s+(?P<status>[45]\d{2})",
    re.IGNORECASE,
)
_EXCEPTION_RE = re.compile(
    r"(?P<exc_type>[\w.]+(?:Error|Exception|Denied|NotFound|Invalid|Exist|Conflict|Unavailable)[:\s].*)",
    re.MULTILINE,
)
_TRACEBACK_FILE_RE = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<func>\S+)')


def _extract_http_error(log_text: str) -> Optional[Dict[str, Any]]:
    match = _HTTP_ERROR_RE.search(log_text)
    if match:
        return {
            "method": match.group("method"),
            "path": match.group("path"),
            "status_code": int(match.group("status")),
        }
    return None


def _extract_traceback_frames(log_text: str) -> List[Dict[str, str]]:
    return [
        {"file": m.group("file"), "line": m.group("line"), "function": m.group("func")}
        for m in _TRACEBACK_FILE_RE.finditer(log_text)
    ]


def _extract_exception_type(log_text: str) -> Optional[str]:
    match = _EXCEPTION_RE.search(log_text)
    return match.group("exc_type").split(":")[0].strip() if match else None


class DjangoParser(BasePlugin):
    """Parses Django error logs and enriches the agent state with structured context."""

    metadata = PluginMetadata(
        name="django_parser",
        version="1.0.0",
        author="responseiq-core",
        log_format="Django",
        description="Extracts HTTP request errors, ORM exceptions, and traceback frames from Django logs.",
    )

    @classmethod
    def can_handle(cls, log_text: str) -> bool:
        return any(sig in log_text for sig in _DJANGO_SIGNALS)

    def run(self, agent_state: dict) -> dict:
        """Extract Django-specific context from ``agent_state["messages"]``."""
        messages: List[str] = agent_state.get("messages", [])
        combined = "\n".join(str(m) for m in messages)

        http_error = _extract_http_error(combined)
        frames = _extract_traceback_frames(combined)
        exc_type = _extract_exception_type(combined)

        parsed: Dict[str, Any] = {
            "framework": "django",
            "exception_type": exc_type,
            "traceback_frames": frames,
        }
        if http_error:
            parsed["http_error"] = http_error

        return {"parsed_context": parsed}
