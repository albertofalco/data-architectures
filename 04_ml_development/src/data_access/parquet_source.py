"""Parquet implementation of feature table access."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path

import polars as pl


# ==================== MAIN CLASSES ====================

class ParquetFeatureSource:
    """Load DW report tables from local parquet files."""

    def __init__(self, data_dir: Path):
        """Initialize the source with its parquet data directory."""
        self.data_dir = data_dir

    def load_table(
        self,
        table_name: str,
        limit: int | None = None,
        entity_ids: list[int | str] | None = None,
        entity_key: str | None = None,
    ) -> pl.LazyFrame:
        """Load a parquet table, resolving `rep_` aliases and optional row filters."""
        stem = Path(table_name).stem
        candidates = [self.data_dir / f"{stem}.parquet"]
        if not stem.startswith("rep_"):
            candidates.append(self.data_dir / f"rep_{stem}.parquet")

        for path in candidates:
            if path.exists():
                frame = pl.scan_parquet(path)
                if entity_ids is not None and entity_key is not None:
                    frame = frame.filter(pl.col(entity_key).is_in(entity_ids))
                return frame.limit(limit) if limit else frame

        raise FileNotFoundError(f"Parquet table not found for `{table_name}` in {self.data_dir}")
