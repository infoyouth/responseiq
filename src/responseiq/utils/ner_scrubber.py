# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""NER-based PII scrubber using spaCy (P7: zero-knowledge context).

Complements the regex scrubber with spaCy ``en_core_web_sm`` entity
recognition to catch PERSON, ORG, and location names that patterns miss.
A no-op (safe import) when ``settings.ner_scrub_enabled = False`` or
spaCy is not installed — the regex scrubber still runs unchanged.
"""

from __future__ import annotations

import threading
from typing import Dict, Optional, Tuple

from responseiq.utils.logger import logger

# ---------------------------------------------------------------------------
# spaCy NLP singleton — loaded once per process, thread-safe via lock
# ---------------------------------------------------------------------------

_NLP_LOCK = threading.Lock()
_NLP: Optional[object] = None  # spacy.Language | None
_NLP_LOAD_ATTEMPTED = False  # avoid re-trying after a failed load

_SCRUB_LABELS = {
    "PERSON": "PERSON",
    "ORG": "ORG",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "FAC": "LOCATION",
    "PRODUCT": "PRODUCT",
    "MONEY": "FINANCIAL",
    "DATE": "DATE",
    "TIME": "TIME",
    "CARDINAL": "NUMBER",
    "NORP": "GROUP",
}


def _load_nlp() -> Optional[object]:
    """Load spaCy model once; return None on failure."""
    global _NLP, _NLP_LOAD_ATTEMPTED  # noqa: PLW0603
    with _NLP_LOCK:
        if _NLP_LOAD_ATTEMPTED:
            return _NLP
        _NLP_LOAD_ATTEMPTED = True
        try:
            import spacy  # type: ignore[import-untyped]

            _NLP = spacy.load("en_core_web_sm")
            logger.info("P7 NER scrubber: spaCy en_core_web_sm loaded")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "P7 NER scrubber: spaCy unavailable — falling back to regex scrubber",
                error=str(exc),
            )
            _NLP = None
    return _NLP


def scrub_with_ner(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Replace named entities in *text* with opaque placeholders.

    Returns
    -------
    scrubbed_text : The sanitised payload safe to send to an LLM.
    mapping       : placeholder → original value for local ``restore_ner()``.

    If spaCy is unavailable, returns ``(text, {})`` — the regex path in
    ``log_scrubber.scrub()`` will still run afterward.
    """
    nlp = _load_nlp()
    if nlp is None:
        return text, {}

    try:
        doc = nlp(text)  # type: ignore[operator]
    except Exception as exc:  # noqa: BLE001
        logger.warning("P7 NER scrubber: inference failed", error=str(exc))
        return text, {}

    mapping: Dict[str, str] = {}
    counter: Dict[str, int] = {}
    replacements: list[tuple[int, int, str]] = []

    for ent in doc.ents:
        label = _SCRUB_LABELS.get(ent.label_)
        if label is None:
            continue  # safe entity type — leave as-is

        original = ent.text
        # De-duplicate: same value → same placeholder
        existing = next((ph for ph, v in mapping.items() if v == original), None)
        if existing:
            replacements.append((ent.start_char, ent.end_char, existing))
            continue

        count = counter.get(label, 0) + 1
        counter[label] = count
        placeholder = f"<REDACTED_{label}_{count}>"
        mapping[placeholder] = original
        replacements.append((ent.start_char, ent.end_char, placeholder))

    if not replacements:
        return text, {}

    # Apply replacements right-to-left so offsets stay valid
    scrubbed = text
    for start, end, placeholder in sorted(replacements, key=lambda x: x[0], reverse=True):
        scrubbed = scrubbed[:start] + placeholder + scrubbed[end:]

    return scrubbed, mapping


def restore_ner(text: str, mapping: Dict[str, str]) -> str:
    """Reverse a previous ``scrub_with_ner()`` call."""
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text
