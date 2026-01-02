"""
CornerGuide - BJJ Rules Assistant

Main entry point for the application.
Handles logging setup and application launch.
"""

import logging
import sys

from config import LOG_DATE_FORMAT, LOG_FORMAT, LOG_LEVEL
from startup.validation import validate_environment
from ui.streamlit_ui import run_ui


def setup_logging():
    """Initialize structured logging for CornerGuide."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)


def main():
    """Main application entry point."""
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting CornerGuide application")

    # Validate environment
    if not validate_environment():
        logger.critical("Environment validation failed - exiting")
        sys.exit(1)

    # Launch UI
    logger.info("Launching Streamlit UI")
    run_ui()


if __name__ == "__main__":
    main()
