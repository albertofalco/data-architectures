"""Path helpers for the ML pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from common.config import configured_path


def ml_path(config: dict[str, Any], key: str, default: str) -> Path:
    """Resolve and create a configured ML output path."""
    path = configured_path(config, key, default)
    path.mkdir(parents=True, exist_ok=True)
    return path


def feature_output_path(config: dict[str, Any]) -> Path:
    """Return the configured engineered feature parquet path."""
    output_dir = ml_path(config, "features", "./data/ml_outputs/features/")
    filename = config.get("ml_pipeline", {}).get(
        "feature_output", "application_train_features.parquet"
    )
    return output_dir / filename
