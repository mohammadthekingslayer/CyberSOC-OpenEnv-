"""Logging utilities for CyberSOC OpenEnv."""

from __future__ import annotations

import logging
import sys

from ..config import get_settings


def setup_logging(name: str = "cybersoc") -> logging.Logger:
    """Configure and return a logger.

    Args:
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    settings = get_settings()
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
