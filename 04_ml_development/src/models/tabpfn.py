"""TabPFN-3 foundation model adapter."""

from __future__ import annotations

from pathlib import Path

import joblib


class TabPFN3Model:
    """TabPFN classifier adapter."""

    name = "tabpfn_3"

    def __init__(self, config: dict):
        try:
            from tabpfn import TabPFNClassifier
        except ImportError as error:
            raise RuntimeError("Missing dependency `tabpfn` for TabPFN-3.") from error
        self.model = TabPFNClassifier()

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
