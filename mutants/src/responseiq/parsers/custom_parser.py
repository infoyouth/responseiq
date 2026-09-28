# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Keyword-based log parser driven by project configuration.

Reads a keyword list from ``settings`` and flags any log line that
contains a match. Acts as the catch-all parser when no language-specific
plugin claims the line first.
"""

import json
from typing import Any, Dict, Optional

from responseiq.config.settings import settings

from .base import BaseParser
from .registry import registry


class KeywordParser(BaseParser):
    """
    Parser that uses configurable keywords to identify events.
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self.reload_config()

    def reload_config(self) -> None:
        cfg_path = settings.get_keywords_config_path()
        if not cfg_path.exists():
            # Set defaults if config is missing
            self._config = {
                "simple": [
                    "error",
                    "exception",
                    "failed",
                    "panic",
                    "critical",
                    "timeout",
                ],
                "events": {
                    "oomkilled": "OOMKilled",
                    "crashloop": "CrashLoopBackOff",
                    "502": "Nginx502",
                },
                "mapping": {
                    "high": ["panic", "critical", "oomkilled", "crashloop"],
                    "medium": ["error", "exception", "failed", "timeout"],
                },
            }
            return

        with open(cfg_path, "r", encoding="utf-8") as fh:
            self._config = json.load(fh)

    def can_handle(self, log_line: str) -> bool:
        # Check both events and simple keywords
        txt = log_line.lower()
        events = self._config.get("events", {})
        simple = self._config.get("simple", [])
        return any(k in txt for k in events) or any(k in txt for k in simple)

    def parse(self, log_line: str) -> Optional[Dict[str, Any]]:
        txt = log_line.lower()
        events = self._config.get("events", {})
        mapping = self._config.get("mapping", {})
        simple = self._config.get("simple", [])

        # Priority 1: Events
        for k, title in events.items():
            if k in txt:
                severity = "medium"
                for sev, kws in mapping.items():
                    if k in kws:
                        severity = sev
                        break
                return {"title": title, "severity": severity, "raw": log_line}

        # Priority 2: Simple Keywords
        for k in simple:
            if k in txt:
                severity = "medium"
                for sev, kws in mapping.items():
                    if k in kws:
                        severity = sev
                        break
                return {
                    "title": k,  # Title is just the keyword
                    "severity": severity,
                    "raw": log_line,
                }

        return None


# Auto-register on import
registry.register(KeywordParser)
