"""Test helpers for the deployment module."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "05_deployment" / "scripts"
API_DIR = REPO_ROOT / "05_deployment" / "api"


for path in (str(SCRIPTS_DIR), str(API_DIR), str(REPO_ROOT / "04_ml_development" / "src")):
    if path not in sys.path:
        sys.path.insert(0, path)


def load_script_module(name: str):
    """Load a deployment script as an importable module."""
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def deployment_config(tmp_path: Path) -> dict:
    """Return a deployment config backed by temporary paths."""
    return {
        "paths": {
            "raw_application_train": str(tmp_path / "raw" / "application_train.csv"),
            "dw_application_train": str(tmp_path / "dw" / "rep_application_train.parquet"),
            "normalized_application_train": str(tmp_path / "db_input" / "application_train.csv"),
            "holdout_ids": str(tmp_path / "assets" / "holdout_ids.csv"),
            "holdout_truth": str(tmp_path / "assets" / "holdout_truth.csv"),
            "inference_runs": str(tmp_path / "runs"),
            "predictions": str(tmp_path / "predictions"),
            "metrics": str(tmp_path / "metrics"),
            "models": str(tmp_path / "models"),
        },
        "defaults": {
            "entity_key": "SK_ID_CURR",
            "target": "TARGET",
            "source_name": "clickhouse",
            "insert_table": "application_train",
            "run_id_prefix": "test",
            "batch_size": 2,
            "models": ["xgboost"],
        },
        "clickhouse": {
            "database": "data_arch_dw",
            "staging_database": "staging_mysql",
            "predictions_table": "ml_predictions",
        },
        "mysql": {"table": "application_train"},
    }
