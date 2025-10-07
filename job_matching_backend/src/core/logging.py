import logging
import os


# PUBLIC_INTERFACE
def configure_logging(level: str | int | None = None) -> None:
    """Configure root logger for the application."""
    level_value = level or os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level_value,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
