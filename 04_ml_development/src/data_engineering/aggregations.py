"""Reusable table aggregation functions."""

# ==================== IMPORTS ====================

from __future__ import annotations

import polars as pl

from data_engineering.schemas import TECHNICAL_COLUMNS, feature_name


# ==================== CONFIGURATION ====================

NUMERIC_DTYPES = {
    pl.Int8,
    pl.Int16,
    pl.Int32,
    pl.Int64,
    pl.UInt8,
    pl.UInt16,
    pl.UInt32,
    pl.UInt64,
    pl.Float32,
    pl.Float64,
}


# ==================== HELPER FUNCTIONS ====================

def _numeric_columns(frame: pl.LazyFrame, key: str, excluded: set[str]) -> list[str]:
    """Get numeric columns from the frame, excluding technical columns and the key."""
    schema = frame.collect_schema()
    return [
        name
        for name, dtype in schema.items()
        if dtype in NUMERIC_DTYPES and name not in excluded and name != key
    ]


def _categorical_columns(frame: pl.LazyFrame, key: str, excluded: set[str]) -> list[str]:
    """Get categorical columns from the frame, excluding technical columns and the key."""
    schema = frame.collect_schema()
    return [
        name
        for name, dtype in schema.items()
        if dtype == pl.String and name not in excluded and name != key
    ]


# ==================== MAIN FUNCTIONS ====================

def aggregate_by_key(
    frame: pl.LazyFrame,
    key: str,
    prefix: str,
    excluded_columns: set[str] | None = None,
) -> pl.LazyFrame:
    """Aggregate a one-to-many table into one row per entity key."""
    excluded = set(excluded_columns or set()) | TECHNICAL_COLUMNS
    numeric_columns = _numeric_columns(frame, key=key, excluded=excluded)
    categorical_columns = _categorical_columns(frame, key=key, excluded=excluded)

    aggregations: list[pl.Expr] = [pl.len().alias(f"{prefix}__row_count")]
    for column in numeric_columns:
        aggregations.extend(
            [
                pl.col(column).mean().alias(feature_name(prefix, column, "mean")),
                pl.col(column).min().alias(feature_name(prefix, column, "min")),
                pl.col(column).max().alias(feature_name(prefix, column, "max")),
                pl.col(column).sum().alias(feature_name(prefix, column, "sum")),
                pl.col(column).std().alias(feature_name(prefix, column, "std")),
            ]
        )

    for column in categorical_columns:
        aggregations.append(pl.col(column).n_unique().alias(feature_name(prefix, column, "nunique")))

    return frame.group_by(key).agg(aggregations)


def aggregate_bureau_balance(
    balance: pl.LazyFrame,
    bureau: pl.LazyFrame,
    bridge_key: str,
    entity_key: str,
    prefix: str,
) -> pl.LazyFrame:
    """Aggregate bureau balance through bureau using the configured entity key."""
    balance_by_bureau = aggregate_by_key(balance, key=bridge_key, prefix=f"{prefix}_by_bureau")
    bridge = bureau.select([entity_key, bridge_key]).unique()
    joined = bridge.join(balance_by_bureau, on=bridge_key, how="left")
    return aggregate_by_key(
        joined,
        key=entity_key,
        prefix=prefix,
        excluded_columns={bridge_key},
    )
