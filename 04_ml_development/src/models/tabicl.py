"""TabICL foundation model adapter."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path

import joblib


# ==================== MAIN CLASSES ====================

class TabICLModel:
    """TabICL classifier adapter."""

    name = "tabicl"

    def __init__(self, config: dict):
        """Initialize the TabICL classifier from pipeline configuration."""
        try:
            from tabicl import TabICLClassifier
        except ImportError as error:
            raise RuntimeError("Missing dependency `tabicl` for TabICL.") from error

        ml_config = config.get("ml_pipeline", {})
        params = ml_config.get("models", {}).get("tabicl", {})
        self.model = TabICLClassifier(
            n_estimators=params.get("n_estimators", 8),
            batch_size=params.get("batch_size", 4),
            offload_mode=params.get("offload_mode", "auto"),
            disk_offload_dir=params.get("disk_offload_dir"),
            n_jobs=params.get("n_jobs"),
            verbose=params.get("verbose", False),
            random_state=ml_config.get("random_state", 42),
        )

    def fit(self, X, y):
        """Fit the TabICL classifier and return this adapter."""
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
