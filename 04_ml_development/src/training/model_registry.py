"""Local model artifact registry helpers."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path
from typing import Any

from common.config import configured_path


# ==================== HELPER FUNCTIONS ====================

def model_artifact_path(config: dict[str, Any], model_name: str) -> Path:
    """Return the local artifact path for a model bundle."""
    output_dir = configured_path(config, "models", "./data/ml_outputs/models/")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{model_name}_bundle.joblib"


def save_bundle(config: dict[str, Any], model_name: str, bundle: dict[str, Any]) -> Path:
    """Serialize a model bundle to the local registry with joblib."""
    import joblib

    path = model_artifact_path(config, model_name)
    joblib.dump(bundle, path)
    return path


def load_bundle(path: Path) -> dict[str, Any]:
    """Load a joblib-serialized model bundle from the local registry."""
    import joblib

    return joblib.load(path)
