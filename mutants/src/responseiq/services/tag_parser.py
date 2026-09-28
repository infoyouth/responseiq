# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""XML/HTML tag block extractor.

Parses ``<tag>...</tag>`` blocks from LLM response text using
``BeautifulSoup``. Used to pull structured sections (e.g.
``<patch>``, ``<rationale>``) out of free-form LLM output reliably.
"""

from typing import Optional

from bs4 import BeautifulSoup


def extract_tag_block(text: str, tag: str) -> Optional[str]:
    """
    Extracts the content of the first <tag>...</tag> block from text.
    Returns None if not found.
    Ignores leading/trailing whitespace and nested tags.
    Tag matching is case-insensitive.
    """
    soup = BeautifulSoup(text, "lxml")
    found = soup.find(tag.lower())
    if found:
        return found.get_text(strip=True)
    return None


# Example usage:
# patch = extract_tag_block(llm_output, "PATCH")
# test = extract_tag_block(llm_output, "REPRO_TEST")
