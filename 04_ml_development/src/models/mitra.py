"""Mitra foundation model adapter."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from common.config import resolve_project_path


class MitraModel:
    """AutoGluon Mitra classifier adapter."""

    name = "mitra"

    def __init__(self, config: dict):
        try:
            from autogluon.tabular import TabularPredictor
        except ImportError as error:
            raise RuntimeError("Missing dependency `autogluon.tabular` for Mitra.") from error

        self.TabularPredictor = TabularPredictor
        self.config = config
        self.predictor = None
        self.feature_limit = None

    @staticmethod
    def _as_dataframe(X) -> pd.DataFrame:
        """Return features in the DataFrame format expected by AutoGluon."""
        if isinstance(X, pd.DataFrame):
            return X.reset_index(drop=True)
        return pd.DataFrame(X)

    def _limit_features(self, X: pd.DataFrame) -> pd.DataFrame:
        if self.feature_limit is None:
            return X
        return X.iloc[:, : self.feature_limit]

    def fit(self, X, y):
        target = self.config.get("ml_pipeline", {}).get("target", "TARGET")
        params = self.config.get("ml_pipeline", {}).get("models", {}).get("mitra", {})
        self.feature_limit = params.get("feature_limit", None)
        predictor_path = resolve_project_path(
            params.get("predictor_path", "data/ml_outputs/models/autogluon/mitra/")
        )
        predictor_path.mkdir(parents=True, exist_ok=True)
        X_df = self._limit_features(self._as_dataframe(X))
        y_series = pd.Series(y).reset_index(drop=True).rename(target)
        train_data = pd.concat([X_df, y_series], axis=1)
        mitra_params = {"fine_tune": params.get("fine_tune", True)}
        if "max_features" in params:
            mitra_params["ag.max_features"] = params["max_features"]
        self.predictor = self.TabularPredictor(
            label=target,
            problem_type="binary",
            path=str(predictor_path),
        ).fit(
            train_data,
            presets="best_quality",
            hyperparameters={"MITRA": mitra_params},
            time_limit=params.get("time_limit", 3600),
            dynamic_stacking=params.get("dynamic_stacking", "auto"),
            num_bag_folds=params.get("num_bag_folds", None),
            num_stack_levels=params.get("num_stack_levels", None),
        )
        return self

    def predict(self, X):
        return self.predictor.predict(self._limit_features(self._as_dataframe(X))).to_numpy()

    def predict_proba(self, X):
        return self.predictor.predict_proba(self._limit_features(self._as_dataframe(X))).to_numpy()

    def save(self, path: Path) -> Path:
        if self.predictor is None:
            raise RuntimeError("Cannot save an unfitted Mitra model.")
        return Path(self.predictor.path)
