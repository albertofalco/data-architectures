"""Training use case orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from common.config import configured_path
from common.mlflow_tracking import log_metrics, setup_mlflow
from common.paths import feature_output_path
from common.timing import PerformanceLogger
from models.base import make_model
from preprocessing.column_selection import split_features_target
from preprocessing.pipeline import build_preprocessor
from preprocessing.split import train_validation_test_split
from training.evaluate_model import evaluate_adapter
from training.model_registry import save_bundle


def train_model(
    config: dict[str, Any],
    model_name: str,
    features_path: Path | None = None,
) -> Path:
    """Train one model family and persist its complete inference bundle."""
    performance = PerformanceLogger()
    features_path = features_path or feature_output_path(config)
    df = pd.read_parquet(features_path)
    performance.snapshot_memory("after_read_features")
    X, y = split_features_target(df, config=config, require_target=True)
    if y is None:
        raise ValueError("Training requires a target column.")

    X_train, X_val, X_test, y_train, y_val, y_test = train_validation_test_split(X, y, config)
    performance.snapshot_memory("after_split")
    preprocessor = build_preprocessor(X_train, config)

    with performance.timed("preprocess_fit_seconds"):
        X_train_prepared = preprocessor.fit_transform(X_train)
        X_val_prepared = preprocessor.transform(X_val)
        X_test_prepared = preprocessor.transform(X_test)
    performance.snapshot_memory("after_preprocessing")

    adapter = make_model(model_name, config)
    with performance.timed("train_seconds"):
        adapter.fit(X_train_prepared, y_train)
    performance.snapshot_memory("after_fit")

    with performance.timed("validation_predict_seconds"):
        validation_metrics = evaluate_adapter(
            adapter, X_val_prepared, y_val, metric_prefix="validation_"
        )
    performance.snapshot_memory("after_validation_predict")

    with performance.timed("test_predict_seconds"):
        test_metrics = evaluate_adapter(adapter, X_test_prepared, y_test, metric_prefix="test_")
    performance.snapshot_memory("after_test_predict")

    metrics = {
        "model": model_name,
        "train_rows": len(X_train),
        "validation_rows": len(X_val),
        "test_rows": len(X_test),
        **validation_metrics,
        **test_metrics,
        **performance.metrics,
    }

    bundle = {
        "model_name": model_name,
        "adapter": adapter,
        "preprocessor": preprocessor,
        "feature_columns": X.columns.tolist(),
        "target": config.get("ml_pipeline", {}).get("target", "TARGET"),
        "metrics": metrics,
    }
    artifact_path = save_bundle(config, model_name, bundle)

    metrics_dir = configured_path(config, "metrics", "./data/ml_outputs/metrics/")
    performance.metrics.update(metrics)
    performance.write_json(metrics_dir / f"{model_name}_training_metrics.json")

    mlflow = setup_mlflow(config)
    if mlflow is not None:
        with mlflow.start_run(run_name=model_name):
            mlflow.log_param("model_name", model_name)
            mlflow.log_artifact(str(artifact_path))
            log_metrics(mlflow, metrics)

    return artifact_path
