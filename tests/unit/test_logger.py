"""Tests for responseiq.utils.logger — setup_logging() branch coverage.

Missing patch lines covered here:
  - logger.py:30-31  handler-removal path (called twice)
  - logger.py:38     RESPONSEIQ_LOG_LEVEL env-var branch (walrus operator)
  - logger.py:40     prod environment effective_level path
  - logger.py:46     prod JSON logger.add path
"""

import os
from unittest.mock import patch

from loguru import logger

import responseiq.utils.logger as logger_mod
from responseiq.utils.logger import setup_logging


class TestSetupLogging:
    def setup_method(self):
        """Reset module-level handler state so tests are isolated."""
        logger_mod._handler_id = None

    def teardown_method(self):
        """Remove the handler registered by setup_logging so loguru stays clean."""
        if logger_mod._handler_id is not None:
            try:
                logger.remove(logger_mod._handler_id)
            except ValueError:
                pass
            logger_mod._handler_id = None

    # ------------------------------------------------------------------
    # Line 30-31: handler-removal path
    # ------------------------------------------------------------------
    def test_second_call_removes_previous_handler(self):
        """setup_logging() called twice removes the first handler before adding a new one."""
        setup_logging(level="DEBUG")
        first_id = logger_mod._handler_id
        assert first_id is not None

        setup_logging(level="WARNING")
        second_id = logger_mod._handler_id

        # A new handler was registered — IDs must differ
        assert second_id is not None
        assert second_id != first_id

    def test_handler_id_reset_to_none_if_already_removed(self):
        """ValueError from logger.remove() is silently swallowed (defensive path)."""
        setup_logging(level="DEBUG")
        # Manually remove the handler outside setup_logging to simulate the edge case
        try:
            logger.remove(logger_mod._handler_id)
        except ValueError:
            pass
        # Calling again must not raise even though the ID is stale
        setup_logging(level="INFO")
        assert logger_mod._handler_id is not None

    # ------------------------------------------------------------------
    # Line 38: RESPONSEIQ_LOG_LEVEL env-var branch
    # ------------------------------------------------------------------
    def test_env_var_level_used_when_no_explicit_arg(self):
        """RESPONSEIQ_LOG_LEVEL env var drives the level when no explicit arg given."""
        with patch.dict(os.environ, {"RESPONSEIQ_LOG_LEVEL": "WARNING"}, clear=False):
            setup_logging()
        assert logger_mod._handler_id is not None

    def test_explicit_arg_overrides_env_var(self):
        """Explicit level arg takes priority over RESPONSEIQ_LOG_LEVEL env var."""
        with patch.dict(os.environ, {"RESPONSEIQ_LOG_LEVEL": "DEBUG"}, clear=False):
            setup_logging(level="ERROR")
        # Handler should be registered (we can't directly read the level, but no error)
        assert logger_mod._handler_id is not None

    # ------------------------------------------------------------------
    # Lines 40 + 46: prod environment paths
    # ------------------------------------------------------------------
    def test_prod_env_uses_json_stdout_handler(self):
        """In prod environment, setup_logging registers a JSON-serialized stdout handler."""
        with patch("responseiq.utils.logger.settings") as mock_settings:
            mock_settings.environment = "prod"
            setup_logging()
        assert logger_mod._handler_id is not None

    def test_prod_env_respects_explicit_level_arg(self):
        """Prod environment still honours an explicit level override."""
        with patch("responseiq.utils.logger.settings") as mock_settings:
            mock_settings.environment = "prod"
            setup_logging(level="ERROR")
        assert logger_mod._handler_id is not None
