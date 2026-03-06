"""src/responseiq/plugins/base.py

P5.2: Plugin SDK base interface.

Every log-parser plugin must subclass ``BasePlugin``, declare a ``metadata``
class attribute of type ``PluginMetadata``, and implement both ``can_handle``
and ``run``.

Discovery
─────────
``PluginRegistry`` (``plugin_registry.py``) auto-discovers all subclasses that
live in the ``src/responseiq/plugins/`` directory via ``pkgutil.iter_modules``.

Writing a custom plugin
───────────────────────
    from responseiq.plugins.base import BasePlugin, PluginMetadata

    class MyParser(BasePlugin):
        metadata = PluginMetadata(
            name="my_parser",
            version="1.0.0",
            author="you@example.com",
            log_format="my-framework",
            description="Parses MyFramework error logs.",
        )

        @classmethod
        def can_handle(cls, log_text: str) -> bool:
            return "MyFramework" in log_text

        def run(self, agent_state: dict) -> dict:
            # Extract relevant info and return delta
            return {"parsed_framework": "my-framework"}
"""

from __future__ import annotations

import json
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

# Patterns that indicate tool-version headers, bare paths, or OS strings —
# none of which carry actionable signal for the LLM.
_NOISE_HEADER_RE = re.compile(
    r"^("
    r"HTTPie \d|Requests \d|Pygments \d|Python \d"
    r"|Linux \S|Windows \S|Darwin \S"
    r"|/\S+$"  # bare filesystem paths with no spaces
    r")"
)
# Object repr blocks: <ClassName { ... }> emitted by debug modes
_REPR_BLOCK_START_RE = re.compile(r"^<[A-Z][A-Za-z]+ \{")


@dataclass
class PluginMetadata:
    """Declarative metadata attached to every plugin class."""

    name: str
    version: str
    author: str
    log_format: str
    description: str = ""


class BasePlugin(ABC):
    """Abstract base class for all ResponseIQ log-parser plugins."""

    #: Subclasses MUST define this class attribute.
    metadata: PluginMetadata

    @classmethod
    def can_handle(cls, log_text: str) -> bool:  # noqa: ARG003
        """Return ``True`` if this plugin can meaningfully parse *log_text*.

        Override in each concrete plugin.  The default implementation returns
        ``False`` so unimplemented plugins are never auto-selected.
        """
        return False

    @staticmethod
    def _filter_noise_lines(lines: List[str]) -> List[str]:
        """Strip tool-version headers and object-repr dump blocks from log lines.

        Keeps error lines, tracebacks, and stack frames (the signal).
        Removes: version headers (``HTTPie 3.2.4``, ``Python 3.12``), bare
        filesystem paths, OS strings, and multi-line ``<Object {...}>`` repr
        blocks emitted by ``--debug`` flags.

        This dramatically improves LLM focus when log files include verbose
        debug preambles (e.g. ``http --debug``, Django DEBUG=True, etc.).
        """
        result: List[str] = []
        in_repr_block = False
        brace_depth = 0

        for line in lines:
            if in_repr_block:
                brace_depth += line.count("{") - line.count("}")
                if brace_depth <= 0:
                    in_repr_block = False
                continue

            if _REPR_BLOCK_START_RE.match(line):
                brace_depth = line.count("{") - line.count("}")
                # Only enter block-skip mode when the block spans multiple lines;
                # if braces balance on this single line, skip only this line.
                if brace_depth > 0:
                    in_repr_block = True
                continue

            if _NOISE_HEADER_RE.match(line):
                continue

            result.append(line)

        return result

    @staticmethod
    def _read_stdin() -> List[str]:
        """Read log messages from stdin.

        Accepts three wire formats piped via ``--target -``:

        1. **NDJSON** — one JSON object per line, each with a ``message`` key::

               {"level": "ERROR", "message": "KeyError: 'email'"}
               {"level": "CRITICAL", "message": "OOM — 2.1 GB RSS"}

        2. **JSON array** — a single array of objects with a ``message`` key::

               [{"message": "..."}, {"message": "..."}]

        3. **Plain text** — one log line per stdin line (the familiar case)::

               echo "ERROR: ZeroDivisionError" | responseiq --mode scan --target -

        All three formats are detected automatically; no flag required.
        """
        raw = sys.stdin.read()
        if not raw.strip():
            return []

        messages: List[str] = []

        # ── Try NDJSON (one JSON object per line) ──────────────────────────
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        ndjson_hits: List[str] = []
        for line in lines:
            if line.startswith("{"):
                try:
                    obj = json.loads(line)
                    msg = obj.get("message") or obj.get("msg") or obj.get("text") or obj.get("body")
                    if msg:
                        ndjson_hits.append(str(msg))
                        continue
                except json.JSONDecodeError:
                    pass
            # not parseable as JSON object — treat as plain-text line
            ndjson_hits.append(line)

        if ndjson_hits:
            return ndjson_hits

        # ── Try JSON array ─────────────────────────────────────────────────
        stripped = raw.strip()
        if stripped.startswith("["):
            try:
                data = json.loads(stripped)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            msg = item.get("message") or item.get("msg") or item.get("text")
                            if msg:
                                messages.append(str(msg))
                    if messages:
                        return messages
            except json.JSONDecodeError:
                pass

        # ── Fallback: plain text lines ─────────────────────────────────────
        return [ln.strip() for ln in raw.splitlines() if ln.strip()]

    @abstractmethod
    def run(self, agent_state: dict) -> dict:
        """Run the plugin with the provided agent state.

        Returns a *delta* dict that is merged into the agent state by the
        caller.  Only include keys that the plugin wishes to set or update.
        """
