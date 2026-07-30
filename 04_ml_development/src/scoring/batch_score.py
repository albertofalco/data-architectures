"""Production-style batch scoring use case."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from common.config import configured_path
from common.timing import PerformanceLogger
from data_engineering.build_features import make_source
from data_engineering.feature_builder import FeatureBuilder
from preprocessing.column_selection import entity_ids, split_features_target
from training.evaluate_model import positive_class_scores
from training.model_registry import load_bundle


# ==================== MAIN FUNCTIONS ====================

def batch_score(
    config: dict[str, Any],
    model_uri: Path,
    source_name: str = "clickhouse",
    limit: int | None = None,
    entity_id_values: list[int | str] | None = None,
    output_suffix: str = "batch_predictions",
) -> Path:
    """Score a production batch and persist predictions plus timing metrics."""
    performance = PerformanceLogger()
    bundle = load_bundle(model_uri)
    source = make_source(source_name, config)
    builder = FeatureBuilder(source=source, config=config)

    with performance.timed("production_extract_transform_seconds"):
        df = builder.collect(limit=limit, entity_ids=entity_id_values).to_pandas()

    ids = entity_ids(df, config)
    X, _ = split_features_target(df, config=config, require_target=False)
    X = X.reindex(columns=bundle["feature_columns"], fill_value=0)

    with performance.timed("production_transform_seconds"):
        X_prepared = bundle["preprocessor"].transform(X)

    with performance.timed("production_predict_seconds"):
        adapter = bundle["adapter"]
        predictions = adapter.predict(X_prepared)
        scores = positive_class_scores(adapter.predict_proba(X_prepared))

    total_seconds = (
        float(performance.metrics.get("production_extract_transform_seconds", 0.0))
        + float(performance.metrics.get("production_transform_seconds", 0.0))
        + float(performance.metrics.get("production_predict_seconds", 0.0))
    )
    performance.add("production_total_seconds", round(total_seconds, 6))
    performance.add("batch_size", len(X))
    if entity_id_values is not None:
        performance.add("requested_entity_ids", len(entity_id_values))
    performance.add_throughput(rows=len(X), total_seconds_metric="production_total_seconds")

    predictions_dir = configured_path(config, "predictions", "./data/ml_outputs/predictions/")
    predictions_dir.mkdir(parents=True, exist_ok=True)
    output_path = predictions_dir / f"{bundle['model_name']}_{output_suffix}.parquet"
    result = pd.DataFrame(
        {
            config.get("ml_pipeline", {}).get("entity_key", "SK_ID_CURR"): ids,
            "score": scores,
            "prediction": predictions,
            "model_name": bundle["model_name"],
        }
    )
    result.to_parquet(output_path, index=False)

    metrics_dir = configured_path(config, "metrics", "./data/ml_outputs/metrics/")
    performance.write_json(metrics_dir / f"{bundle['model_name']}_{output_suffix}_metrics.json")
    return output_path
