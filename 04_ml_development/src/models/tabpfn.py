"""TabPFN-3 foundation model adapter."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path

import joblib


# ==================== MAIN CLASSES ====================

class TabPFN3Model:
    """TabPFN classifier adapter."""

    name = "tabpfn_3"

    def __init__(self, config: dict):
        """Initialize the TabPFN classifier."""
        try:
            from tabpfn import TabPFNClassifier
        except ImportError as error:
            raise RuntimeError("Missing dependency `tabpfn` for TabPFN-3.") from error
        self.model = TabPFNClassifier()

    def fit(self, X, y):
        """Fit the TabPFN classifier and return this adapter."""
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
