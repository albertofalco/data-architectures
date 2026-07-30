"""Scikit-learn preprocessing pipeline factories."""

# ==================== IMPORTS ====================

from __future__ import annotations

from typing import Any

import pandas as pd

from preprocessing.encoders import categorical_encoder
from preprocessing.imputers import categorical_imputer, numeric_imputer


# ==================== HELPER FUNCTIONS ====================

def build_preprocessor(X: pd.DataFrame, config: dict[str, Any]):
    """Build a transformer with imputation, numeric scaling, and categorical encoding."""
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    categorical_min_frequency = (
        config.get("ml_pipeline", {})
        .get("preprocessing", {})
        .get("categorical_min_frequency", 10)
    )
    numeric_columns = X.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_columns = [column for column in X.columns if column not in numeric_columns]

    transformers = []
    if numeric_columns:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", numeric_imputer()),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_columns,
            )
        )
    if categorical_columns:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", categorical_imputer()),
                        ("encoder", categorical_encoder(categorical_min_frequency)),
                    ]
                ),
                categorical_columns,
            )
        )

    return ColumnTransformer(transformers=transformers, remainder="drop")
