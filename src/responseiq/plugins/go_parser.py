"""src/responseiq/plugins/go_parser.py

P5.2 built-in parser: Go runtime panic and error logs.

Detects and extracts structured context from Go logs:
  - Runtime panics (goroutine dumps)
  - ``panic: <message>`` lines
  - ``goroutine N [running]:`` headers
  - Standard Go stack frames (pkg/file.go:line)
  - ``log.Fatal`` / ``log.Panic`` / ``zap`` / ``logrus`` log output
  - Signal-based crashes (SIGSEGV, SIGABRT)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from responseiq.plugins.base import BasePlugin, PluginMetadata

# ── signatures ───────────────────────────────────────────────────────────────
_GO_SIGNALS: List[str] = [
    "goroutine ",
    "panic: ",
    "runtime error:",
    "SIGSEGV",
    "SIGABRT",
    "signal: ",
    "[signal ",
    "created by ",
    ".go:",
]

# ── patterns ─────────────────────────────────────────────────────────────────
_PANIC_MSG_RE = re.compile(r"^panic:\s+(?P<msg>.+)$", re.MULTILINE)
_RUNTIME_ERR_RE = re.compile(r"runtime error:\s+(?P<err>.+)", re.MULTILINE)
_GOROUTINE_HEADER_RE = re.compile(r"goroutine\s+(?P<id>\d+)\s+\[(?P<state>[^\]]+)\]:")
_FRAME_RE = re.compile(
    r"^(?P<func>[\w./()[\]*-]+)\((?P<args>[^)]*)\)\n\s+(?P<file>[^\s:]+\.go):(?P<line>\d+)",
    re.MULTILINE,
)
_SIGNAL_RE = re.compile(r"signal:\s+(?P<sig>\w+)|received signal\s+(?P<sig2>\w+)", re.IGNORECASE)
_CREATED_BY_RE = re.compile(r"created by\s+(?P<creator>[\w./]+)")


def _extract_panic_message(log_text: str) -> Optional[str]:
    match = _PANIC_MSG_RE.search(log_text)
    return match.group("msg").strip() if match else None


def _extract_runtime_error(log_text: str) -> Optional[str]:
    match = _RUNTIME_ERR_RE.search(log_text)
    return match.group("err").strip() if match else None


def _extract_goroutines(log_text: str) -> List[Dict[str, str]]:
    return [{"id": m.group("id"), "state": m.group("state")} for m in _GOROUTINE_HEADER_RE.finditer(log_text)]


def _extract_stack_frames(log_text: str) -> List[Dict[str, str]]:
    return [
        {"function": m.group("func"), "file": m.group("file"), "line": m.group("line")}
        for m in _FRAME_RE.finditer(log_text)
    ]


def _extract_signal(log_text: str) -> Optional[str]:
    match = _SIGNAL_RE.search(log_text)
    if match:
        return match.group("sig") or match.group("sig2")
    return None


class GoParser(BasePlugin):
    """Parses Go runtime panic and error logs and enriches the agent state."""

    metadata = PluginMetadata(
        name="go_parser",
        version="1.0.0",
        author="responseiq-core",
        log_format="Go",
        description=(
            "Extracts panic messages, runtime errors, goroutine states, "
            "stack frames, and signal crashes from Go runtime logs."
        ),
    )

    @classmethod
    def can_handle(cls, log_text: str) -> bool:
        return any(sig in log_text for sig in _GO_SIGNALS)

    def run(self, agent_state: dict) -> dict:
        messages: List[str] = agent_state.get("messages", [])
        combined = "\n".join(str(m) for m in messages)

        panic_msg = _extract_panic_message(combined)
        runtime_err = _extract_runtime_error(combined)
        goroutines = _extract_goroutines(combined)
        frames = _extract_stack_frames(combined)
        signal = _extract_signal(combined)
        creators = [m.group("creator") for m in _CREATED_BY_RE.finditer(combined)]

        parsed: Dict[str, Any] = {
            "framework": "go",
            "panic_message": panic_msg,
            "runtime_error": runtime_err or panic_msg,
            "signal": signal,
            "goroutines": goroutines,
            "stack_frames": frames[:20],
            "top_frame": frames[0] if frames else None,
            "goroutine_creators": creators,
            "crash_type": (
                "signal" if signal else "panic" if panic_msg else "runtime_error" if runtime_err else "unknown"
            ),
        }
        return {"parsed_context": parsed}
