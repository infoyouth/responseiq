"""
tests/unit/test_ner_scrubber.py — P7: spaCy NER Scrubbing v2
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers: build a minimal spaCy doc mock
# ---------------------------------------------------------------------------


def _make_ent(text: str, label_: str, start_char: int, end_char: int) -> SimpleNamespace:
    return SimpleNamespace(text=text, label_=label_, start_char=start_char, end_char=end_char)


def _make_nlp_mock(entities):
    """Return a callable that produces a spaCy-like doc with given entities."""
    doc = SimpleNamespace(ents=entities)
    nlp = MagicMock(return_value=doc)
    return nlp


# ---------------------------------------------------------------------------
# Fixture: reset module-level singleton before each test
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_ner_singleton():
    """Reset the NLP singleton so each test starts clean."""
    import responseiq.utils.ner_scrubber as mod

    original_nlp = mod._NLP
    original_attempted = mod._NLP_LOAD_ATTEMPTED
    mod._NLP = None
    mod._NLP_LOAD_ATTEMPTED = False
    yield
    mod._NLP = original_nlp
    mod._NLP_LOAD_ATTEMPTED = original_attempted


# ---------------------------------------------------------------------------
# Tests: graceful degradation (spaCy unavailable)
# ---------------------------------------------------------------------------


class TestNERScrubberUnavailable:
    def test_returns_original_text_when_spacy_missing(self):
        # Simulate spaCy load having been attempted and failed (_NLP stays None)
        import responseiq.utils.ner_scrubber as mod

        mod._NLP = None
        mod._NLP_LOAD_ATTEMPTED = True  # already tried, no model available
        from responseiq.utils.ner_scrubber import scrub_with_ner

        text = "John Smith called from 192.168.1.1"
        result, mapping = scrub_with_ner(text)
        assert result == text
        assert mapping == {}

    def test_returns_empty_mapping_on_spacy_missing(self):
        import responseiq.utils.ner_scrubber as mod

        mod._NLP = None
        mod._NLP_LOAD_ATTEMPTED = True  # mark as attempted+failed
        from responseiq.utils.ner_scrubber import scrub_with_ner

        _, mapping = scrub_with_ner("some log line")
        assert mapping == {}


# ---------------------------------------------------------------------------
# Tests: NER scrubbing (spaCy mocked)
# ---------------------------------------------------------------------------


class TestNERScrubberWithMock:
    def _setup_nlp(self, entities):
        import responseiq.utils.ner_scrubber as mod

        mod._NLP = _make_nlp_mock(entities)
        mod._NLP_LOAD_ATTEMPTED = True

    def test_person_entity_scrubbed(self):
        self._setup_nlp([_make_ent("Alice Johnson", "PERSON", 0, 13)])
        from responseiq.utils.ner_scrubber import scrub_with_ner

        text = "Alice Johnson deployed the service"
        scrubbed, mapping = scrub_with_ner(text)
        assert "Alice Johnson" not in scrubbed
        assert "<REDACTED_PERSON_1>" in scrubbed
        assert mapping["<REDACTED_PERSON_1>"] == "Alice Johnson"

    def test_org_entity_scrubbed(self):
        self._setup_nlp([_make_ent("Acme Corp", "ORG", 10, 19)])
        from responseiq.utils.ner_scrubber import scrub_with_ner

        text = "deployed by Acme Corp at 3pm"
        scrubbed, mapping = scrub_with_ner(text)
        assert "Acme Corp" not in scrubbed
        assert "<REDACTED_ORG_1>" in scrubbed

    def test_gpe_entity_scrubbed_as_location(self):
        self._setup_nlp([_make_ent("New York", "GPE", 5, 13)])
        from responseiq.utils.ner_scrubber import scrub_with_ner

        text = "from New York datacenter"
        scrubbed, mapping = scrub_with_ner(text)
        assert "New York" not in scrubbed
        assert "<REDACTED_LOCATION_1>" in scrubbed

    def test_safe_entity_label_not_scrubbed(self):
        # LANGUAGE is in the safe-list — should not be replaced
        self._setup_nlp([_make_ent("Python", "LANGUAGE", 0, 6)])
        from responseiq.utils.ner_scrubber import scrub_with_ner

        text = "Python runtime error"
        scrubbed, mapping = scrub_with_ner(text)
        assert scrubbed == text
        assert mapping == {}

    def test_duplicate_entity_same_placeholder(self):
        # "Bob triggered an alert. Bob"
        #  0                       24^^
        self._setup_nlp(
            [
                _make_ent("Bob", "PERSON", 0, 3),
                _make_ent("Bob", "PERSON", 24, 27),
            ]
        )
        from responseiq.utils.ner_scrubber import scrub_with_ner

        text = "Bob triggered an alert. Bob"
        scrubbed, mapping = scrub_with_ner(text)
        # Only one PERSON placeholder should exist
        assert list(mapping.keys()).count("<REDACTED_PERSON_1>") == 1
        # Both occurrences replaced
        assert "Bob" not in scrubbed

    def test_multiple_entity_types_numbered_independently(self):
        self._setup_nlp(
            [
                _make_ent("Carol", "PERSON", 0, 5),
                _make_ent("Google", "ORG", 18, 24),
            ]
        )
        from responseiq.utils.ner_scrubber import scrub_with_ner

        text = "Carol is an SRE at Google"
        scrubbed, mapping = scrub_with_ner(text)
        assert "<REDACTED_PERSON_1>" in scrubbed
        assert "<REDACTED_ORG_1>" in scrubbed

    def test_restore_ner_reverses_scrub(self):
        self._setup_nlp([_make_ent("Dave", "PERSON", 0, 4)])
        from responseiq.utils.ner_scrubber import restore_ner, scrub_with_ner

        original = "Dave caused the outage"
        scrubbed, mapping = scrub_with_ner(original)
        restored = restore_ner(scrubbed, mapping)
        assert restored == original

    def test_no_entities_returns_original_unchanged(self):
        self._setup_nlp([])
        from responseiq.utils.ner_scrubber import scrub_with_ner

        text = "NullPointerException at line 42"
        scrubbed, mapping = scrub_with_ner(text)
        assert scrubbed == text
        assert mapping == {}


# ---------------------------------------------------------------------------
# Tests: log_scrubber integration with ner_scrub_enabled
# ---------------------------------------------------------------------------


class TestLogScrubberNERIntegration:
    def test_ner_scrub_disabled_by_default(self):
        """With ner_scrub_enabled=False (default), NER path must not be called."""
        with patch("responseiq.config.settings.settings") as mock_settings:
            mock_settings.ner_scrub_enabled = False
            mock_settings.scrub_enabled = True
            from responseiq.utils import log_scrubber

            importlib.reload(log_scrubber)
            # Patch ner_scrubber to detect if it gets called
            with patch("responseiq.utils.ner_scrubber.scrub_with_ner") as mock_ner:
                log_scrubber.scrub("some log with sk-abc1234567890abcdef text")
                mock_ner.assert_not_called()

    def test_ner_scrub_enabled_calls_ner_path(self):
        """When ner_scrub_enabled=True, scrub() must invoke scrub_with_ner."""
        with patch("responseiq.config.settings.settings") as mock_settings:
            mock_settings.ner_scrub_enabled = True
            from responseiq.utils import log_scrubber

            importlib.reload(log_scrubber)
            with patch("responseiq.utils.ner_scrubber.scrub_with_ner", return_value=("cleaned text", {})) as mock_ner:
                log_scrubber.scrub("some log text")
                mock_ner.assert_called_once_with("some log text")
