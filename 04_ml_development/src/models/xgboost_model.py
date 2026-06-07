"""XGBoost model adapter."""

from __future__ import annotations

from pathlib import Path

import joblib


class XGBoostModel:
    """XGBClassifier adapter with CPU default and GPU-compatible config."""

    name = "xgboost"

    def __init__(self, config: dict):
        try:
            from xgboost import XGBClassifier
        except ImportError as error:
            raise RuntimeError("Missing dependency `xgboost`.") from error

        ml_config = config.get("ml_pipeline", {})
        params = ml_config.get("models", {}).get("xgboost", {})
        self.model = XGBClassifier(
            n_estimators=params.get("n_estimators", 300),
            max_depth=params.get("max_depth", 5),
            learning_rate=params.get("learning_rate", 0.05),
            eval_metric=params.get("eval_metric", "logloss"),
            tree_method=params.get("tree_method", "hist"),
            random_state=ml_config.get("random_state", 42),
        )

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        return path
