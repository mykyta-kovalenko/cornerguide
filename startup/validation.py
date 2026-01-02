"""Environment validation for CornerGuide."""

import logging
import os

logger = logging.getLogger(__name__)


def validate_environment() -> bool:
    """
    Validate required environment variables are set.

    Returns:
        bool: True if all required vars present, False otherwise
    """
    required_vars = ["OPENAI_API_KEY", "COHERE_API_KEY"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.critical(
            "Missing required environment variables - application cannot start",
            extra={"missing_vars": missing_vars}
        )
        return False

    logger.info("Environment validation passed")
    return True
