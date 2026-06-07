"""Train/validation/test split helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd


def train_validation_test_split(
    X: pd.DataFrame,
    y: pd.Series,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Create stratified train, validation, and test splits."""
    from sklearn.model_selection import train_test_split

    ml_config = config.get("ml_pipeline", {})
    split_config = ml_config.get("split", {})
    random_state = ml_config.get("random_state", 42)
    test_size = split_config.get("test_size", 0.2)
    validation_size = split_config.get("validation_size", 0.2)
    stratify_enabled = split_config.get("stratify", True)

    stratify = y if stratify_enabled else None
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )

    validation_fraction = validation_size / (1.0 - test_size)
    stratify_train_val = y_train_val if stratify_enabled else None
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=validation_fraction,
        random_state=random_state,
        stratify=stratify_train_val,
    )
    return X_train, X_val, X_test, y_train, y_val, y_test
