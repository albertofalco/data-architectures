"""Optuna objective factories."""

from __future__ import annotations

import time
from typing import Any

from common.timing import PerformanceLogger
from models.base import make_model
from preprocessing.column_selection import split_features_target
from preprocessing.pipeline import build_preprocessor
from preprocessing.split import train_validation_test_split
from training.evaluate_model import evaluate_adapter


def objective_for_model(model_name: str, df, config: dict[str, Any]):
    """Create a simple validation PR-AUC objective for supported local models."""
    X, y = split_features_target(df, config=config, require_target=True)
    X_train, X_val, _, y_train, y_val, _ = train_validation_test_split(X, y, config)

    def objective(trial):
        trial_config = dict(config)
        ml_config = dict(config.get("ml_pipeline", {}))
        models_config = dict(ml_config.get("models", {}))
        params = dict(models_config.get(model_name, {}))

        if model_name == "random_forest":
            params["n_estimators"] = trial.suggest_int("n_estimators", 50, 400)
            params["max_depth"] = trial.suggest_int("max_depth", 3, 20)
        elif model_name == "xgboost":
            params["n_estimators"] = trial.suggest_int("n_estimators", 50, 500)
            params["max_depth"] = trial.suggest_int("max_depth", 2, 10)
            params["learning_rate"] = trial.suggest_float("learning_rate", 0.01, 0.2, log=True)
        elif model_name == "local_neural_net":
            params["epochs"] = trial.suggest_int("epochs", 5, 50)
            params["learning_rate"] = trial.suggest_float("learning_rate", 1e-4, 1e-2, log=True)
        elif model_name == "tabicl":
            params["n_estimators"] = trial.suggest_categorical("n_estimators", [2, 4, 8])
            params["batch_size"] = trial.suggest_categorical("batch_size", [2, 4])
            params["offload_mode"] = "auto"
            params["verbose"] = True
        elif model_name == "tabpfn_mix":
            params["max_epochs"] = trial.suggest_categorical("max_epochs", [0, 1])
            params["n_ensembles"] = trial.suggest_categorical("n_ensembles", [1, 2, 4])
            params["dynamic_stacking"] = False
            params["num_bag_folds"] = 0
            params["num_stack_levels"] = 0
            params["fit_weighted_ensemble"] = False
            params["predictor_path"] = (
                "./data/ml_outputs/models/autogluon/tabpfn_mix_tuning/"
                f"trial_{trial.number:02d}/"
            )
        elif model_name == "pyod_autoencoder":
            params["contamination"] = trial.suggest_categorical("contamination", [0.05, 0.081])
            params["epoch_num"] = trial.suggest_categorical("epoch_num", [10, 20])
            params["hidden_neuron_list"] = trial.suggest_categorical(
                "hidden_neuron_list",
                [[64, 32, 32, 64], [128, 64, 64, 128]],
            )
            params["train_normals_only"] = True
            params["batch_size"] = 256
            params["learning_rate"] = 0.001
            params["random_state"] = ml_config.get("random_state", 42)
            params["verbose"] = 0
        else:
            raise ValueError(f"Tuning is not supported for model: {model_name}")

        models_config[model_name] = params
        ml_config["models"] = models_config
        trial_config["ml_pipeline"] = ml_config

        started_at = time.perf_counter()
        performance = PerformanceLogger()
        preprocessor = build_preprocessor(X_train, trial_config)
        X_train_prepared = preprocessor.fit_transform(X_train)
        X_val_prepared = preprocessor.transform(X_val)
        adapter = make_model(model_name, trial_config)
        performance.snapshot_memory("before_fit")
        with performance.timed("fit_seconds"):
            adapter.fit(X_train_prepared, y_train)
        performance.snapshot_memory("after_fit")
        with performance.timed("validation_predict_seconds"):
            metrics = evaluate_adapter(
                adapter,
                X_val_prepared,
                y_val,
                metric_prefix="validation_",
            )
        performance.snapshot_memory("after_validation_predict")
        performance.add("trial_seconds", round(time.perf_counter() - started_at, 6))
        if model_name in {"tabicl", "tabpfn_mix", "pyod_autoencoder"}:
            for metric_name, value in {**metrics, **performance.metrics}.items():
                trial.set_user_attr(metric_name, value)
        return metrics["validation_pr_auc"]

    return objective
