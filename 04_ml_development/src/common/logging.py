"""Logging configuration helpers."""

# ==================== IMPORTS ====================

from __future__ import annotations

import logging


# ==================== HELPER FUNCTIONS ====================

def get_logger(name: str) -> logging.Logger:
    """Return an INFO logger, adding the default handler when none exists."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
