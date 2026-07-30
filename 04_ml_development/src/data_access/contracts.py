"""Data access contracts."""

# ==================== IMPORTS ====================

from __future__ import annotations

from typing import Protocol

import polars as pl


# ==================== MAIN CLASSES ====================

class FeatureSource(Protocol):
    """Source capable of loading a named feature table."""

    def load_table(
        self,
        table_name: str,
        limit: int | None = None,
        entity_ids: list[int | str] | None = None,
        entity_key: str | None = None,
    ) -> pl.LazyFrame:
        """Load a lazy table with optional entity filtering and row limiting."""
        ...
