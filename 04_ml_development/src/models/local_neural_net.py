"""Local neural network model adapter."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path

import joblib


# ==================== MAIN CLASSES ====================

class LocalNeuralNetModel:
    """Provide a portable scikit-learn MLP baseline for smoke tests."""

    name = "local_neural_net"

    def __init__(self, config: dict):
        """Initialize the MLP classifier from pipeline configuration."""
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
        """Fit the MLP classifier and return this adapter."""
        self.model.fit(X, y)
        return self

    def predict(self, X):
        """Predict class labels for the supplied features."""
        return self.model.predict(X)

    def predict_proba(self, X):
        """Predict class probabilities for the supplied features."""
        return self.model.predict_proba(X)

    def save(self, path: Path) -> Path:
        """Persist the fitted classifier and return its artifact path."""
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        return path
