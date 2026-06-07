"""Local model artifact registry helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from common.config import configured_path


def model_artifact_path(config: dict[str, Any], model_name: str) -> Path:
    """Return the local artifact path for a model bundle."""
    output_dir = configured_path(config, "models", "./data/ml_outputs/models/")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{model_name}_bundle.joblib"


def save_bundle(config: dict[str, Any], model_name: str, bundle: dict[str, Any]) -> Path:
    """Persist a model bundle."""
    import joblib

    path = model_artifact_path(config, model_name)
    joblib.dump(bundle, path)
    return path


def load_bundle(path: Path) -> dict[str, Any]:
    """Load a persisted model bundle."""
    import joblib

    return joblib.load(path)
