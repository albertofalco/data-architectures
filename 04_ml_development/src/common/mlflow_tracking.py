"""Optional MLflow integration helpers."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path
from typing import Any

from common.config import configured_path


# ==================== HELPER FUNCTIONS ====================

def setup_mlflow(config: dict[str, Any]) -> Any | None:
    """Configure the tracking directory and experiment, or return None without MLflow."""
    try:
        import mlflow
    except ImportError:
        return None

    tracking_dir = configured_path(config, "mlflow_tracking", "./data/ml_outputs/mlruns/")
    tracking_dir.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(tracking_dir.as_uri())

    experiment = config.get("ml_pipeline", {}).get("mlflow", {}).get(
        "experiment_name", "home_credit_default_risk"
    )
    mlflow.set_experiment(experiment)
    return mlflow


def log_metrics(mlflow_module: Any | None, metrics: dict[str, Any]) -> None:
    """Log numeric metrics when an MLflow module is provided."""
    if mlflow_module is None:
        return
    for name, value in metrics.items():
        if isinstance(value, (int, float)):
            mlflow_module.log_metric(name, value)
