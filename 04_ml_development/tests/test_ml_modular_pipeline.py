"""Unit tests for the modular ML pipeline layers."""

# ==================== IMPORTS ====================

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import polars as pl

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from common.timing import PerformanceLogger
from data_access.parquet_source import ParquetFeatureSource
from data_engineering.feature_builder import FeatureBuilder
from models.pyod_autoencoder import PyODAutoEncoderModel
from preprocessing.column_selection import split_features_target
from training.evaluate_model import positive_class_scores


# ==================== TEST FUNCTIONS ====================

def test_parquet_source_loads_rep_prefixed_table(tmp_path: Path) -> None:
    """Load a report table through its unprefixed logical name."""
    path = tmp_path / "rep_application_train.parquet"
    pl.DataFrame({"SK_ID_CURR": [1], "TARGET": [0]}).write_parquet(path)

    source = ParquetFeatureSource(tmp_path)
    assert source.load_table("application_train").collect().shape == (1, 2)


def test_parquet_source_filters_entity_ids(tmp_path: Path) -> None:
    """Filter parquet rows to the requested entity identifiers."""
    path = tmp_path / "rep_bureau.parquet"
    pl.DataFrame({"SK_ID_CURR": [1, 2, 3], "AMT": [10.0, 20.0, 30.0]}).write_parquet(path)

    source = ParquetFeatureSource(tmp_path)
    result = source.load_table("rep_bureau", entity_ids=[1, 3], entity_key="SK_ID_CURR").collect()

    assert result["SK_ID_CURR"].to_list() == [1, 3]


def test_feature_builder_returns_one_row_per_entity(tmp_path: Path) -> None:
    """Build a feature table containing one row per entity."""
    pl.DataFrame(
        {
            "SK_ID_CURR": [1, 2],
            "TARGET": [0, 1],
            "AMT_CREDIT": [100.0, 200.0],
        }
    ).write_parquet(tmp_path / "rep_application_train.parquet")
    pl.DataFrame(
        {
            "SK_ID_CURR": [1, 1, 2],
            "SK_ID_BUREAU": [10, 11, 20],
            "AMT_CREDIT_SUM": [5.0, 7.0, 9.0],
            "CREDIT_ACTIVE": ["Active", "Closed", "Active"],
        }
    ).write_parquet(tmp_path / "rep_bureau.parquet")

    config = {
        "ml_pipeline": {
            "entity_key": "SK_ID_CURR",
            "target": "TARGET",
            "base_table": "rep_application_train",
            "feature_tables": {
                "bureau": {
                    "table": "rep_bureau",
                    "key": "SK_ID_CURR",
                    "prefix": "bureau",
                }
            },
        }
    }
    features = FeatureBuilder(ParquetFeatureSource(tmp_path), config).collect()

    assert features.height == 2
    assert features["SK_ID_CURR"].n_unique() == 2
    assert "bureau__row_count" in features.columns


def test_split_features_target_excludes_target_and_technical_ids() -> None:
    """Exclude the target and configured technical identifiers from features."""
    df = pd.DataFrame(
        {
            "SK_ID_CURR": [1, 2],
            "TARGET": [0, 1],
            "_DW_ID": [100, 200],
            "feature": [1.5, 2.5],
        }
    )
    config = {
        "ml_pipeline": {
            "target": "TARGET",
            "preprocessing": {"exclude_columns": ["_DW_ID", "SK_ID_CURR"]},
        }
    }
    X, y = split_features_target(df, config)

    assert list(X.columns) == ["feature"]
    assert y is not None
    assert y.tolist() == [0, 1]


def test_performance_logger_records_json(tmp_path: Path) -> None:
    """Persist timing and derived throughput metrics as JSON."""
    logger = PerformanceLogger()
    with logger.timed("train_seconds"):
        sum(range(10))
    logger.add_throughput(rows=2, total_seconds_metric="train_seconds")
    output_path = logger.write_json(tmp_path / "metrics.json")

    assert output_path.exists()
    assert "rows_per_second" in output_path.read_text(encoding="utf-8")


def test_pyod_autoencoder_adapter_uses_normal_rows_and_scores(monkeypatch) -> None:
    """Train the anomaly adapter on normal rows and expose class scores."""

    class FakeAutoEncoder:
        """Provide a deterministic PyOD test double."""

        fitted_rows = None

        def __init__(self, **kwargs):
            """Capture initialization arguments and initialize score state."""
            self.kwargs = kwargs
            self.decision_scores_ = None

        def fit(self, X):
            """Record the fitted row count and fixed training scores."""
            FakeAutoEncoder.fitted_rows = len(X)
            self.decision_scores_ = pd.Series([0.1, 0.2, 0.3]).to_numpy()
            return self

        def predict(self, X):
            """Return deterministic binary anomaly labels."""
            return pd.Series([0, 1, 0, 1]).to_numpy()[: len(X)]

        def decision_function(self, X):
            """Return deterministic anomaly scores."""
            return pd.Series([0.1, 0.2, 0.3, 0.4]).to_numpy()[: len(X)]

    import types

    fake_pyod = types.ModuleType("pyod")
    fake_models = types.ModuleType("pyod.models")
    fake_auto_encoder = types.ModuleType("pyod.models.auto_encoder")
    fake_auto_encoder.AutoEncoder = FakeAutoEncoder
    monkeypatch.setitem(sys.modules, "pyod", fake_pyod)
    monkeypatch.setitem(sys.modules, "pyod.models", fake_models)
    monkeypatch.setitem(sys.modules, "pyod.models.auto_encoder", fake_auto_encoder)

    config = {
        "ml_pipeline": {
            "random_state": 42,
            "models": {
                "pyod_autoencoder": {
                    "train_normals_only": True,
                    "contamination": 0.25,
                    "epoch_num": 1,
                    "batch_size": 2,
                    "verbose": 0,
                }
            },
        }
    }
    adapter = PyODAutoEncoderModel(config)
    X = pd.DataFrame({"feature_a": [1.0, 2.0, 3.0, 4.0], "feature_b": [1.5, 2.5, 3.5, 4.5]})
    y = pd.Series([0, 1, 0, 0])

    adapter.fit(X, y)
    predictions = adapter.predict(X)
    probabilities = adapter.predict_proba(X)

    assert FakeAutoEncoder.fitted_rows == 3
    assert predictions.shape == (4,)
    assert probabilities.shape == (4, 2)
    assert positive_class_scores(probabilities).shape == (4,)
