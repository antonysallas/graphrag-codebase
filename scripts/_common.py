"""Shared utilities for CLI scripts."""

import sys
from pathlib import Path

from loguru import logger


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


def setup_logging(level: str = "INFO") -> None:
    """Configure loguru with specified level.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    logger.remove()
    logger.add(sys.stderr, level=level.upper())
