"""Use case for building engineered features."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path
from typing import Any

from common.config import configured_path
from common.paths import feature_output_path
from common.timing import PerformanceLogger
from data_access.clickhouse_source import ClickHouseFeatureSource
from data_access.parquet_source import ParquetFeatureSource
from data_engineering.feature_builder import FeatureBuilder


# ==================== HELPER FUNCTIONS ====================

def make_source(source_name: str, config: dict[str, Any]):
    """Create a feature source adapter from a source name."""
    if source_name == "parquet":
        return ParquetFeatureSource(configured_path(config, "dw_data", "./data/dw_parquet/"))
    if source_name == "clickhouse":
        return ClickHouseFeatureSource()
    raise ValueError(f"Unsupported source: {source_name}")


# ==================== MAIN FUNCTIONS ====================

def build_features(
    config: dict[str, Any],
    source_name: str = "parquet",
    output_path: Path | None = None,
    limit: int | None = None,
) -> Path:
    """Build and persist engineered features with construction metrics."""
    performance = PerformanceLogger()
    source = make_source(source_name, config)
    builder = FeatureBuilder(source=source, config=config)
    destination = output_path or feature_output_path(config)

    with performance.timed("feature_build_seconds"):
        features = builder.collect(limit=limit)

    destination.parent.mkdir(parents=True, exist_ok=True)
    features.write_parquet(destination)
    performance.add("rows", features.height)
    performance.add("columns", features.width)

    metrics_dir = configured_path(config, "metrics", "./data/ml_outputs/metrics/")
    performance.write_json(metrics_dir / "feature_build_metrics.json")
    return destination
