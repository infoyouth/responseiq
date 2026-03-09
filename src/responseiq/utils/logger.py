import os
import sys
from typing import Optional

from loguru import logger

from responseiq.config.settings import settings

# Track the handler ID added by setup_logging so we only remove our own,
# never handlers added by tests or other libraries.
_handler_id: Optional[int] = None


def setup_logging(level: str | None = None) -> None:
    """
    Configure Loguru to replace standard logging and output JSON in production.

    The effective log level is resolved in this priority order:
      1. ``level`` argument (explicit override, e.g. from CLI --log-level)
      2. ``RESPONSEIQ_LOG_LEVEL`` environment variable
      3. ``"INFO"`` in production, ``"DEBUG"`` otherwise
    """
    global _handler_id

    # Remove only the handler we previously registered, not all handlers.
    # This prevents wiping handlers added by pytest, fixtures, or other libraries.
    if _handler_id is not None:
        try:
            logger.remove(_handler_id)
        except ValueError:
            pass  # already removed
        _handler_id = None

    effective_level: str
    if level:
        effective_level = level.upper()
    elif env_level := os.environ.get("RESPONSEIQ_LOG_LEVEL", ""):
        effective_level = env_level.upper()
    elif settings.environment == "prod":
        effective_level = "INFO"
    else:
        effective_level = "DEBUG"

    if settings.environment == "prod":
        # JSON format for DataDog/Splunk
        _handler_id = logger.add(sys.stdout, serialize=True, level=effective_level)
    else:
        # Pretty printing for dev / local
        _handler_id = logger.add(
            sys.stderr,
            colorize=True,
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            level=effective_level,
        )


# Initialize on import — respects RESPONSEIQ_LOG_LEVEL if pre-set in env.
setup_logging()
