"""AutoGluon TabPFNMix foundation model adapter."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from common.config import resolve_project_path


class TabPFNMixModel:
    """AutoGluon TabPFNMix classifier adapter."""

    name = "tabpfn_mix"

    def __init__(self, config: dict):
        try:
            from autogluon.tabular import TabularPredictor
        except ImportError as error:
            raise RuntimeError("Missing dependency `autogluon.tabular` for TabPFNMix.") from error

        self.TabularPredictor = TabularPredictor
        self.config = config
        self.predictor = None
        self.predictor_path = None

    @staticmethod
    def _as_dataframe(X) -> pd.DataFrame:
        """Return features in the DataFrame format expected by AutoGluon."""
        if isinstance(X, pd.DataFrame):
            return X.reset_index(drop=True)
        return pd.DataFrame(X)

    def fit(self, X, y):
        target = self.config.get("ml_pipeline", {}).get("target", "TARGET")
        params = self.config.get("ml_pipeline", {}).get("models", {}).get("tabpfn_mix", {})
        predictor_path = resolve_project_path(
            params.get("predictor_path", "data/ml_outputs/models/autogluon/tabpfn_mix/")
        )
        predictor_path.mkdir(parents=True, exist_ok=True)
        self.predictor_path = predictor_path

        X_df = self._as_dataframe(X)
        y_series = pd.Series(y).reset_index(drop=True).rename(target)
        train_data = pd.concat([X_df, y_series], axis=1)

        tabpfn_mix_params = {
            "model_path_classifier": params.get(
                "model_path_classifier", "autogluon/tabpfn-mix-1.0-classifier"
            ),
            "max_epochs": params.get("max_epochs", 0),
            "n_ensembles": params.get("n_ensembles", 1),
        }
        for key in ("max_samples_query", "max_samples_support", "ag.max_rows", "ag.sample_rows"):
            if key in params:
                tabpfn_mix_params[key] = params[key]

        self.predictor = self.TabularPredictor(
            label=target,
            problem_type="binary",
            path=str(predictor_path),
        ).fit(
            train_data,
            hyperparameters={"TABPFNMIX": tabpfn_mix_params},
            time_limit=params.get("time_limit", 3600),
            dynamic_stacking=params.get("dynamic_stacking", False),
            num_bag_folds=params.get("num_bag_folds", 0),
            num_stack_levels=params.get("num_stack_levels", 0),
            fit_weighted_ensemble=params.get("fit_weighted_ensemble", False),
        )
        return self

    def _ensure_predictor(self):
        if self.predictor is None:
            if self.predictor_path is None:
                params = self.config.get("ml_pipeline", {}).get("models", {}).get("tabpfn_mix", {})
                self.predictor_path = resolve_project_path(
                    params.get("predictor_path", "data/ml_outputs/models/autogluon/tabpfn_mix/")
                )
            self.predictor = self.TabularPredictor.load(str(self.predictor_path))
        return self.predictor

    def predict(self, X):
        return self._ensure_predictor().predict(self._as_dataframe(X)).to_numpy()

    def predict_proba(self, X):
        return self._ensure_predictor().predict_proba(self._as_dataframe(X)).to_numpy()

    def save(self, path: Path) -> Path:
        if self.predictor is None:
            raise RuntimeError("Cannot save an unfitted TabPFNMix model.")
        return Path(self.predictor.path)
