"""Hyperparameter tuning use case."""

# ==================== IMPORTS ====================

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from common.config import configured_path
from common.paths import feature_output_path
from tuning.objectives import objective_for_model


# ==================== CONFIGURATION ====================

TABICL_GRID_SEARCH_SPACE = {
    "n_estimators": [2, 4, 8],
    "batch_size": [2, 4],
}

TABPFN_MIX_GRID_SEARCH_SPACE = {
    "max_epochs": [0, 1],
    "n_ensembles": [1, 2, 4],
}

PYOD_AUTOENCODER_GRID_SEARCH_SPACE = {
    "contamination": [0.05, 0.081],
    "epoch_num": [10, 20],
    "hidden_neuron_list": [[64, 32, 32, 64], [128, 64, 64, 128]],
}


# ==================== MAIN CLASSES ====================

class GridTrial:
    """Small trial adapter for dependency-light grid search."""

    def __init__(self, number: int, params: dict[str, Any]):
        """Initialize a trial with its sequence number and fixed parameters."""
        self.number = number
        self.params = params
        self.user_attrs: dict[str, Any] = {}

    def suggest_categorical(self, name: str, choices: list[Any]) -> Any:
        """Return the preselected grid value for a categorical parameter."""
        value = self.params[name]
        if value not in choices:
            raise ValueError(f"Grid value {value!r} is not in choices for {name}.")
        return value

    def set_user_attr(self, name: str, value: Any) -> None:
        """Store per-trial metrics in the same spirit as Optuna user attrs."""
        self.user_attrs[name] = value


# ==================== MAIN FUNCTIONS ====================

def tune_model(config: dict[str, Any], model_name: str, features_path: Path | None = None) -> Path:
    """Run Optuna tuning for a supported model family."""
    features_path = features_path or feature_output_path(config)
    df = pd.read_parquet(features_path)
    if model_name == "tabicl":
        return _tune_grid(config, df, "tabicl", TABICL_GRID_SEARCH_SPACE)
    if model_name == "tabpfn_mix":
        return _tune_grid(config, df, "tabpfn_mix", TABPFN_MIX_GRID_SEARCH_SPACE)
    if model_name == "pyod_autoencoder":
        return _tune_grid(
            config,
            df,
            "pyod_autoencoder",
            PYOD_AUTOENCODER_GRID_SEARCH_SPACE,
        )

    try:
        import optuna
    except ImportError as error:
        raise RuntimeError("Missing dependency `optuna`.") from error

    tuning_config = config.get("ml_pipeline", {}).get("tuning", {})
    n_trials = tuning_config.get("n_trials", 20)
    study = optuna.create_study(direction="maximize")
    study.optimize(
        objective_for_model(model_name, df, config),
        n_trials=n_trials,
        timeout=tuning_config.get("timeout_seconds"),
    )

    output_dir = configured_path(config, "metrics", "./data/ml_outputs/metrics/")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{model_name}_tuning_results.json"
    output_path.write_text(
        study.trials_dataframe().to_json(orient="records", indent=2),
        encoding="utf-8",
    )
    return output_path


# ==================== HELPER FUNCTIONS ====================

def _tune_grid(
    config: dict[str, Any],
    df: pd.DataFrame,
    model_name: str,
    search_space: dict[str, list[Any]],
) -> Path:
    """Run a fixed grid without requiring Optuna in the foundation image."""
    objective = objective_for_model(model_name, df, config)
    records: list[dict[str, Any]] = []
    trial_number = 0
    param_names = list(search_space)
    param_values = [search_space[param_name] for param_name in param_names]
    for combination in _grid_combinations(param_names, param_values):
        trial = GridTrial(number=trial_number, params=combination)
        started_at = time.perf_counter()
        record: dict[str, Any] = {
            "number": trial_number,
            "state": "COMPLETE",
        }
        for param_name, value in combination.items():
            record[f"params_{param_name}"] = value
        try:
            record["value"] = objective(trial)
        except Exception as error:  # pragma: no cover - preserves partial tuning output.
            record["state"] = "FAIL"
            record["value"] = None
            record["error"] = f"{type(error).__name__}: {error}"
        record["duration_seconds"] = round(time.perf_counter() - started_at, 6)
        for metric_name, value in trial.user_attrs.items():
            record[f"user_attrs_{metric_name}"] = value
        records.append(record)
        trial_number += 1

    output_dir = configured_path(config, "metrics", "./data/ml_outputs/metrics/")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{model_name}_tuning_results.json"
    output_path.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def _grid_combinations(
    param_names: list[str],
    param_values: list[list[Any]],
    index: int = 0,
    current: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return cartesian product records for small, explicit grids."""
    current = current or {}
    if index == len(param_names):
        return [dict(current)]

    combinations: list[dict[str, Any]] = []
    param_name = param_names[index]
    for value in param_values[index]:
        current[param_name] = value
        combinations.extend(_grid_combinations(param_names, param_values, index + 1, current))
    current.pop(param_name, None)
    return combinations
