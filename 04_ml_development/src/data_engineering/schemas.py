"""Feature schema constants."""

# ==================== IMPORTS ====================

from __future__ import annotations


# ==================== CONFIGURATION ====================

ENTITY_KEY = "SK_ID_CURR"
TARGET = "TARGET"
TECHNICAL_COLUMNS = {"_DW_ID"}


# ==================== HELPER FUNCTIONS ====================

def feature_name(prefix: str, column: str, statistic: str) -> str:
    """Build a stable feature name."""
    clean_column = column.lower()
    return f"{prefix}__{clean_column}__{statistic}"
