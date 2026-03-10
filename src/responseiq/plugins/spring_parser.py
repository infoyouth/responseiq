# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Spring Boot / Java log parser.

Detects and extracts structured context from Spring Boot logs —
exception chains (``BeanCreationException``, ``NullPointerException``),
startup failures, Spring Security access-denied errors, JPA/Hibernate
SQL exceptions, and Log4j / Logback formatted output.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from responseiq.plugins.base import BasePlugin, PluginMetadata

# ── signatures ───────────────────────────────────────────────────────────────
_SPRING_SIGNALS: List[str] = [
    "org.springframework",
    "com.netflix",
    "springframework.boot",
    "BeanCreationException",
    "HibernateJdbcException",
    "DataIntegrityViolationException",
    "TransactionSystemException",
    "ApplicationContext",
    "Started Application",
    "APPLICATION FAILED TO START",
]

# ── patterns ─────────────────────────────────────────────────────────────────
# e.g.  2024-01-01 10:00:00.123  ERROR 1234 --- [main] o.s.b.SpringApplication : Application run failed
_LOG_LINE_RE = re.compile(
    r"(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+"
    r"(?P<level>ERROR|WARN|INFO|DEBUG|TRACE)\s+\d+\s+---\s+\[(?P<thread>[^\]]+)\]\s+"
    r"(?P<logger>[\w.$]+)\s*:\s+(?P<message>.+)"
)
_EXCEPTION_CLASS_RE = re.compile(
    r"^(?P<exc>(?:org\.|com\.|java\.|javax\.)[\w.]+(?:Exception|Error)(?::\s*.+)?)", re.MULTILINE
)
_AT_FRAME_RE = re.compile(r"\s+at\s+(?P<class>[\w.$]+)\.(?P<method>\w+)\((?P<source>[^)]+)\)")
_CAUSED_BY_RE = re.compile(r"Caused by:\s+(?P<exc>[\w.]+(?:Exception|Error)[^\n]*)", re.MULTILINE)


def _extract_error_lines(log_text: str) -> List[Dict[str, str]]:
    return [
        {
            "timestamp": m.group("ts"),
            "thread": m.group("thread"),
            "logger": m.group("logger"),
            "message": m.group("message"),
        }
        for m in _LOG_LINE_RE.finditer(log_text)
        if m.group("level") == "ERROR"
    ]


def _extract_exception_chain(log_text: str) -> List[str]:
    """Return root exception + all 'Caused by' chain entries."""
    exceptions: List[str] = []
    root = _EXCEPTION_CLASS_RE.search(log_text)
    if root:
        exceptions.append(root.group("exc").strip())
    exceptions.extend(m.group("exc").strip() for m in _CAUSED_BY_RE.finditer(log_text))
    return exceptions


def _extract_stack_frames(log_text: str) -> List[Dict[str, str]]:
    return [
        {"class": m.group("class"), "method": m.group("method"), "source": m.group("source")}
        for m in _AT_FRAME_RE.finditer(log_text)
    ]


def _top_frame(frames: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    return frames[0] if frames else None


class SpringParser(BasePlugin):
    """Parses Spring Boot error logs and enriches the agent state."""

    metadata = PluginMetadata(
        name="spring_parser",
        version="1.0.0",
        author="responseiq-core",
        log_format="Spring Boot",
        description=(
            "Extracts ERROR log lines, Java exception chains, Caused-by hierarchy, "
            "and stack frames from Spring Boot / Logback logs."
        ),
    )

    @classmethod
    def can_handle(cls, log_text: str) -> bool:
        return any(sig in log_text for sig in _SPRING_SIGNALS)

    def run(self, agent_state: dict) -> dict:
        messages: List[str] = agent_state.get("messages", [])
        combined = "\n".join(str(m) for m in messages)

        exc_chain = _extract_exception_chain(combined)
        frames = _extract_stack_frames(combined)

        parsed: Dict[str, Any] = {
            "framework": "spring_boot",
            "exception_chain": exc_chain,
            "root_exception": exc_chain[0] if exc_chain else None,
            "top_stack_frame": _top_frame(frames),
            "stack_frames": frames[:20],  # cap to avoid token bloat
            "error_log_lines": _extract_error_lines(combined),
        }
        return {"parsed_context": parsed}
