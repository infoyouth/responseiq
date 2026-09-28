"""Deterministic fingerprints for grouping equivalent incident logs."""

from __future__ import annotations

import hashlib
import re

_DYNAMIC_VALUE_PATTERNS = (
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f-]{27,}\b", re.IGNORECASE), "<uuid>"),
    (
        re.compile(r"\b\d{4}-\d{2}-\d{2}t\d{2}:\d{2}:\d{2}(?:\.\d+)?z\b", re.IGNORECASE),
        "<timestamp>",
    ),
    (re.compile(r"\b(?:request|trace|span|correlation)[_-]?id\s*[=:]\s*[^\s,]+", re.IGNORECASE), "<correlation>"),
)


def normalize_incident_log(log_text: str) -> str:
    """Normalize volatile metadata while preserving the incident signal."""
    normalized_lines: list[str] = []
    for line in log_text.splitlines():
        normalized = line.strip().lower()
        if not normalized:
            continue
        for pattern, replacement in _DYNAMIC_VALUE_PATTERNS:
            normalized = pattern.sub(replacement, normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        normalized_lines.append(normalized)
    return "\n".join(normalized_lines)


def incident_fingerprint(log_text: str, *, service: str = "") -> str:
    """Return a stable SHA-256 fingerprint for normalized incident content."""
    payload = f"{service.strip().lower()}\n{normalize_incident_log(log_text)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
