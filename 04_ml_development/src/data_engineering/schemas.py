"""Feature schema constants."""

from __future__ import annotations


ENTITY_KEY = "SK_ID_CURR"
TARGET = "TARGET"
TECHNICAL_COLUMNS = {"_DW_ID"}


def feature_name(prefix: str, column: str, statistic: str) -> str:
    """Build a stable feature name."""
    clean_column = column.lower()
    return f"{prefix}__{clean_column}__{statistic}"
