"""Structured logging configuration for the backend.

Call `configure_logging()` once during application startup. Log level is read
from Settings so it can be tuned via the `LOG_LEVEL` env var.
"""

from __future__ import annotations

import logging
import sys
from logging import Logger

from app.config import get_settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

_configured = False


def configure_logging() -> None:
    """Configure root logging. Idempotent."""
    global _configured
    if _configured:
        return

    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Silence overly chatty third-party loggers.
    for noisy in ("httpx", "httpcore", "urllib3", "apscheduler.scheduler"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> Logger:
    """Return a named logger, configuring logging on first use."""
    if not _configured:
        configure_logging()
    return logging.getLogger(name)