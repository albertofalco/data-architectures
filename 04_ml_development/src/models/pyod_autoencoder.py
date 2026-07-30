"""PyOD AutoEncoder anomaly detection adapter."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np


# ==================== MAIN CLASSES ====================

class PyODAutoEncoderModel:
    """Semi-supervised PyOD AutoEncoder adapter for tabular anomaly scoring."""

    name = "pyod_autoencoder"

    def __init__(self, config: dict):
        """Initialize the PyOD autoencoder from pipeline configuration."""
        try:
            from pyod.models.auto_encoder import AutoEncoder
        except ImportError as error:
            raise RuntimeError("Missing dependency `pyod[torch]` for PyOD AutoEncoder.") from error

        ml_config = config.get("ml_pipeline", {})
        params = ml_config.get("models", {}).get("pyod_autoencoder", {})
        self.train_normals_only = bool(params.get("train_normals_only", True))
        self.score_min_: float | None = None
        self.score_max_: float | None = None
        self.model = AutoEncoder(
            contamination=params.get("contamination", 0.081),
            hidden_neuron_list=params.get("hidden_neuron_list", [128, 64, 64, 128]),
            epoch_num=params.get("epoch_num", 20),
            batch_size=params.get("batch_size", 256),
            lr=params.get("learning_rate", params.get("lr", 0.001)),
            random_state=params.get("random_state", ml_config.get("random_state", 42)),
            verbose=params.get("verbose", 1),
        )

    def fit(self, X, y):
        """Fit the detector and capture the training score range."""
        X_fit = X
        if self.train_normals_only:
            y_array = np.asarray(y)
            normal_mask = y_array == 0
            if not normal_mask.any():
                raise ValueError("PyOD AutoEncoder requires at least one TARGET=0 row to fit.")
            X_fit = X[normal_mask] if not hasattr(X, "iloc") else X.iloc[normal_mask]

        self.model.fit(X_fit)
        train_scores = np.asarray(getattr(self.model, "decision_scores_", []), dtype=float)
        if train_scores.size:
            self.score_min_ = float(np.nanmin(train_scores))
            self.score_max_ = float(np.nanmax(train_scores))
        return self

    def predict(self, X):
        """Predict binary anomaly labels for the supplied features."""
        return np.asarray(self.model.predict(X)).reshape(-1)

    def predict_proba(self, X):
        """Return normalized anomaly scores as two-class probabilities."""
        scores = np.asarray(self.model.decision_function(X), dtype=float).reshape(-1)
        probabilities = self._scale_scores(scores)
        return np.column_stack([1.0 - probabilities, probabilities])

    def save(self, path: Path) -> Path:
        """Persist the complete adapter and return its artifact path."""
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    def _scale_scores(self, scores: np.ndarray) -> np.ndarray:
        """Scale anomaly scores to a positive-class probability-like range."""
        score_min = self.score_min_ if self.score_min_ is not None else float(np.nanmin(scores))
        score_max = self.score_max_ if self.score_max_ is not None else float(np.nanmax(scores))
        denominator = score_max - score_min
        if denominator <= 0:
            return np.zeros_like(scores, dtype=float)
        return np.clip((scores - score_min) / denominator, 0.0, 1.0)
