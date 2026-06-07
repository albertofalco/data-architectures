"""Model adapter contracts and factory."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np


class ModelAdapter(Protocol):
    """Common interface for all model families."""

    name: str

    def fit(self, X, y) -> "ModelAdapter":
        """Train the model."""
        ...

    def predict(self, X) -> np.ndarray:
        """Predict labels."""
        ...

    def predict_proba(self, X) -> np.ndarray:
        """Predict positive-class probabilities or class probabilities."""
        ...

    def save(self, path: Path) -> Path:
        """Persist the model artifact."""
        ...


def make_model(model_name: str, config: dict) -> ModelAdapter:
    """Create a model adapter by name."""
    if model_name == "random_forest":
        from models.random_forest import RandomForestModel

        return RandomForestModel(config)
    if model_name == "xgboost":
        from models.xgboost_model import XGBoostModel

        return XGBoostModel(config)
    if model_name == "local_neural_net":
        from models.local_neural_net import LocalNeuralNetModel

        return LocalNeuralNetModel(config)
    if model_name == "mitra":
        from models.mitra import MitraModel

        return MitraModel(config)
    if model_name == "tabpfn_3":
        from models.tabpfn import TabPFN3Model

        return TabPFN3Model(config)
    if model_name == "tabpfn_mix":
        from models.tabpfn_mix import TabPFNMixModel

        return TabPFNMixModel(config)
    if model_name == "tabicl":
        from models.tabicl import TabICLModel

        return TabICLModel(config)
    if model_name == "pyod_autoencoder":
        from models.pyod_autoencoder import PyODAutoEncoderModel

        return PyODAutoEncoderModel(config)
    raise ValueError(f"Unsupported model: {model_name}")
