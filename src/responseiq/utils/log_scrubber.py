# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""PII and secrets scrubbing layer for log payloads.

Scrubs sensitive data from log text before it reaches any external LLM
API, replacing emails, IPs, JWTs, API keys, and high-entropy secrets
with reversible placeholders. Enabled by default via
``settings.scrub_enabled``; disable only for fully air-gapped deployments.
"""

from __future__ import annotations

import re
from typing import Callable, Dict, Tuple

# ---------------------------------------------------------------------------
# Pattern registry — order matters: more specific patterns first
# ---------------------------------------------------------------------------

_PATTERN_REGISTRY: list[Tuple[str, re.Pattern[str]]] = [
    (
        "JWT",
        re.compile(
            r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
            re.IGNORECASE,
        ),
    ),
    (
        "BEARER_TOKEN",
        re.compile(
            r"(?i)(Bearer\s+)[A-Za-z0-9\-._~+/]{20,}",
        ),
    ),
    (
        "OPENAI_KEY",
        re.compile(
            r"sk-[A-Za-z0-9]{20,}",
        ),
    ),
    (
        "AWS_KEY",
        re.compile(
            r"AKIA[0-9A-Z]{16}",
        ),
    ),
    (
        "GENERIC_SECRET",
        re.compile(
            r"(?i)(password|passwd|pwd|secret|api[_-]?key|auth[_-]?key|token|access[_-]?key)"
            r"(\s*[=:]\s*)[\"']?[A-Za-z0-9\-._~+/!@#$%^&*]{8,}[\"']?",
        ),
    ),
    (
        "EMAIL",
        re.compile(
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        ),
    ),
    (
        "IPV4",
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
        ),
    ),
    (
        "IPV6",
        re.compile(
            r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
            r"|(?:[0-9a-fA-F]{1,4}:){1,7}:"
            r"|::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}",
        ),
    ),
    (
        "UUID",
        re.compile(
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        ),
    ),
    (
        "CREDIT_CARD",
        re.compile(
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}"
            r"|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}"
            r"|(?:2131|1800|35\d{3})\d{11})\b",
        ),
    ),
]


def scrub(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Replace all detected PII / secret patterns with opaque placeholders.

    Returns:
        scrubbed_text: The sanitised log/code payload safe to send to an LLM.
        mapping:       Dict mapping placeholder → original value, kept only
                       in local memory so upstream code can call restore() on
                       the LLM response if needed.

    When ``settings.ner_scrub_enabled`` is True, a spaCy NER pass runs first
    (P7) replacing PERSON/ORG/GPE/MONEY/DATE entities before the regex layer.

    Example::

        safe_text, mapping = scrub(raw_log)
        llm_response = await call_llm(safe_text)
        display_text = restore(llm_response, mapping)
    """
    # P7: NER pass (spaCy) — runs before regex so named entities are caught first.
    from responseiq.config.settings import settings as _settings  # local import avoids circular dep

    mapping: Dict[str, str] = {}
    if _settings.ner_scrub_enabled:
        from responseiq.utils.ner_scrubber import scrub_with_ner

        text, ner_mapping = scrub_with_ner(text)
        mapping.update(ner_mapping)

    counter: Dict[str, int] = {}

    def _replace(match: re.Match[str], label: str) -> str:
        original = match.group(0)
        # De-duplicate: same value → same placeholder
        for placeholder, value in mapping.items():
            if value == original:
                return placeholder

        count = counter.get(label, 0) + 1
        counter[label] = count
        placeholder = f"<REDACTED_{label}_{count}>"
        mapping[placeholder] = original
        return placeholder

    for label, pattern in _PATTERN_REGISTRY:
        # GENERIC_SECRET needs special handling to preserve the key name
        if label == "GENERIC_SECRET":

            def _gs_replace(m: re.Match[str], _label: str = label) -> str:
                key_name = m.group(1)
                original = m.group(0)
                for placeholder, value in mapping.items():
                    if value == original:
                        return placeholder
                count = counter.get(_label, 0) + 1
                counter[_label] = count
                placeholder = f"<REDACTED_{key_name.upper()}_{count}>"
                mapping[placeholder] = original
                return placeholder

            text = pattern.sub(_gs_replace, text)
        elif label == "BEARER_TOKEN":
            # Preserve "Bearer " prefix, replace only the token portion
            def _bearer_replace(m: re.Match[str], _label: str = label) -> str:
                prefix = m.group(1)
                token = m.group(0)[len(prefix) :]
                original_token = token
                for placeholder, value in mapping.items():
                    if value == original_token:
                        return prefix + placeholder
                count = counter.get(_label, 0) + 1
                counter[_label] = count
                placeholder = f"<REDACTED_{_label}_{count}>"
                mapping[placeholder] = original_token
                return prefix + placeholder

            text = pattern.sub(_bearer_replace, text)
        else:

            def _make_replacer(lbl: str) -> Callable[[re.Match[str]], str]:
                def _replacer(m: re.Match[str]) -> str:
                    return _replace(m, lbl)

                return _replacer

            text = pattern.sub(_make_replacer(label), text)

    return text, mapping


def restore(text: str, mapping: Dict[str, str]) -> str:
    """
    Reverse a previous scrub() call, substituting placeholders back with
    original values in the LLM response or display text.

    This is intentionally LOCAL-ONLY — never serialize the mapping or send it
    to any external service.
    """
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text
