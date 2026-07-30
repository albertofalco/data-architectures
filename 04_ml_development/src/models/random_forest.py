"""Random Forest model adapter."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path

import joblib


# ==================== MAIN CLASSES ====================

class RandomForestModel:
    """Adapt a scikit-learn random forest to the shared model interface."""

    name = "random_forest"

    def __init__(self, config: dict):
        """Initialize the classifier from pipeline configuration."""
        from sklearn.ensemble import RandomForestClassifier

        ml_config = config.get("ml_pipeline", {})
        params = ml_config.get("models", {}).get("random_forest", {})
        self.model = RandomForestClassifier(
            n_estimators=params.get("n_estimators", 200),
            max_depth=params.get("max_depth"),
            class_weight=params.get("class_weight", "balanced"),
            n_jobs=params.get("n_jobs", -1),
            random_state=ml_config.get("random_state", 42),
        )

    def fit(self, X, y):
        """Fit the random forest and return this adapter."""
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
