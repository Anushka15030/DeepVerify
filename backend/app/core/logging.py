"""Logging configuration."""

from __future__ import annotations

import logging
import sys

from app.core.config import get_settings


def configure_logging(level: str | None = None) -> None:
    """Configure root logging using settings."""
    settings = get_settings()
    log_level = (level or settings.log_level).upper()

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=f"%(asctime)s [%(levelname)s] env={settings.app_env} %(name)s: %(message)s",
        stream=sys.stdout,
        force=True,
    )
