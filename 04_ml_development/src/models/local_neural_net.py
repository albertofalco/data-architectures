"""Local neural network model adapter."""

from __future__ import annotations

from pathlib import Path

import joblib


class LocalNeuralNetModel:
    """A local MLP baseline implemented with sklearn for portable smoke tests."""

    name = "local_neural_net"

    def __init__(self, config: dict):
        from sklearn.neural_network import MLPClassifier

        ml_config = config.get("ml_pipeline", {})
        params = ml_config.get("models", {}).get("local_neural_net", {})
        self.model = MLPClassifier(
            hidden_layer_sizes=tuple(params.get("hidden_units", [256, 128])),
            max_iter=params.get("epochs", 20),
            batch_size=params.get("batch_size", 512),
            learning_rate_init=params.get("learning_rate", 0.001),
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
