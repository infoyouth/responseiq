import sys

from loguru import logger

from responseiq.config.settings import settings


def setup_logging():
    """
    Configure Loguru to replace standard logging and output JSON in production.
    """
    # Remove default handler
    logger.remove()

    # Determine format based on environment
    if settings.environment == "prod":
        # JSON format for DataDog/Splunk
        logger.add(sys.stdout, serialize=True, level="INFO")
    else:
        # Pretty printing for Dev
        logger.add(
            sys.stdout,
            colorize=True,
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            level="DEBUG",
        )


# Initialize on import
setup_logging()
