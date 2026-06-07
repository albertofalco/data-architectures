"""Column selection helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd


def split_features_target(
    df: pd.DataFrame,
    config: dict[str, Any],
    require_target: bool = True,
) -> tuple[pd.DataFrame, pd.Series | None]:
    """Split a feature table into X and y while preventing target leakage."""
    ml_config = config.get("ml_pipeline", {})
    target = ml_config.get("target", "TARGET")
    exclude = set(ml_config.get("preprocessing", {}).get("exclude_columns", []))
    exclude.add(target)

    if target not in df.columns:
        if require_target:
            raise ValueError(f"Target column `{target}` not found.")
        y = None
    else:
        y = df[target]

    drop_columns = [column for column in exclude if column in df.columns]
    return df.drop(columns=drop_columns), y


def entity_ids(df: pd.DataFrame, config: dict[str, Any]) -> pd.Series | None:
    """Return entity ids when present."""
    key = config.get("ml_pipeline", {}).get("entity_key", "SK_ID_CURR")
    return df[key] if key in df.columns else None
