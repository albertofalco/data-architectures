"""Tests for the lightweight deployment API."""

# ==================== IMPORTS ====================

from __future__ import annotations

import json
from pathlib import Path

import pytest

import app.main as api_main
import app.services as api_services


# ==================== HELPER FUNCTIONS ====================

def _write_api_fixtures(config: dict) -> None:
    """Create local run and prediction fixtures."""
    runs_dir = Path(config["paths"]["inference_runs"])
    metrics_dir = Path(config["paths"]["metrics"])
    predictions_dir = Path(config["paths"]["predictions"])
    runs_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    predictions_dir.mkdir(parents=True, exist_ok=True)

    (runs_dir / "run_1.json").write_text(
        json.dumps(
            {
                "run_id": "run_1",
                "status": "manifest_only",
                "rows_selected": 2,
                "rows_inserted": 0,
                "entity_ids": [101, 102],
                "inference": {
                    "status": "scored",
                    "models": [
                        {
                            "model_name": "xgboost",
                            "prediction_path": str(predictions_dir / "xgboost_run_1_predictions.parquet"),
                            "metrics_path": str(metrics_dir / "xgboost_run_1_predictions_metrics.json"),
                            "rows_scored": 2,
                            "inference_seconds": 1.25,
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    (predictions_dir / "xgboost_run_1_predictions.parquet").write_text("placeholder", encoding="utf-8")
    (metrics_dir / "xgboost_run_1_predictions_metrics.json").write_text(
        json.dumps(
            {
                "holdout_precision": 0.5,
                "holdout_recall": 1.0,
                "holdout_f1": 0.666667,
                "holdout_roc_auc": 0.75,
                "holdout_pr_auc": 0.8,
                "truth_rows_matched": 2,
                "truth_status": "evaluated",
                "deployment_inference_seconds": 1.25,
                "rows_per_second": 1.6,
                "avg_latency_ms_per_row": 625.0,
            }
        ),
        encoding="utf-8",
    )


# ==================== TESTS ====================

@pytest.mark.skip(reason="fastapi.testclient.TestClient hangs in this Python 3.14 test environment")
def test_fastapi_testclient_smoke() -> None:
    """Document the intended TestClient smoke coverage for compatible environments."""
    from fastapi.testclient import TestClient

    client = TestClient(api_main.app)
    assert client.get("/health").status_code == 200


def test_api_handlers_read_runs_and_predictions(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API endpoints read local manifests and prediction parquet files."""
    _write_api_fixtures(deployment_config)
    monkeypatch.setattr(api_main, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(
        api_main,
        "list_predictions",
        lambda **_: [
            {"SK_ID_CURR": 101, "score": 0.2, "prediction": 0, "model_name": "xgboost"},
            {"SK_ID_CURR": 102, "score": 0.8, "prediction": 1, "model_name": "xgboost"},
        ],
    )
    assert api_main.health() == {"status": "ok"}
    assert api_main.api_runs()[0]["run_id"] == "run_1"
    assert api_main.api_run("run_1")["entity_ids"] == [101, 102]
    assert len(api_main.api_predictions(run_id="run_1", model_name="xgboost")) == 2


def test_prediction_service_reads_matching_files(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prediction service filters local parquet files and returns rows."""
    predictions_dir = Path(deployment_config["paths"]["predictions"])
    predictions_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = predictions_dir / "xgboost_run_1_predictions.parquet"
    prediction_path.write_text("placeholder", encoding="utf-8")

    def fake_read_parquet(path: Path):
        assert path == prediction_path
        return api_services.pd.DataFrame(
            {
                "SK_ID_CURR": [101],
                "score": [0.2],
                "prediction": [0],
                "model_name": ["xgboost"],
            }
        )

    monkeypatch.setattr(api_services.pd, "read_parquet", fake_read_parquet)

    rows = api_services.list_predictions(deployment_config, run_id="run_1", model_name="xgboost")

    assert rows == [
        {
            "SK_ID_CURR": 101,
            "score": 0.2,
            "prediction": 0,
            "model_name": "xgboost",
            "run_id": "run_1",
        }
    ]


def test_wide_prediction_preview_pivots_three_models(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wide prediction preview returns one row per SK_ID_CURR with model columns."""
    predictions_dir = Path(deployment_config["paths"]["predictions"])
    predictions_dir.mkdir(parents=True, exist_ok=True)
    for model in ("xgboost", "tabpfn_mix", "pyod_autoencoder"):
        (predictions_dir / f"{model}_run_1_predictions.parquet").write_text("placeholder", encoding="utf-8")

    def fake_read_parquet(path: Path):
        model_name = path.name.removesuffix("_run_1_predictions.parquet")
        return api_services.pd.DataFrame(
            {
                "SK_ID_CURR": [102, 101],
                "score": [0.2, 0.8],
                "prediction": [0, 1],
                "model_name": [model_name, model_name],
            }
        )

    monkeypatch.setattr(api_services.pd, "read_parquet", fake_read_parquet)

    rows = api_services.wide_prediction_preview(deployment_config, "run_1")

    assert rows == [
        {
            "SK_ID_CURR": 101,
            "xgboost_score": 0.8,
            "xgboost_prediction": 1,
            "tabpfn_mix_score": 0.8,
            "tabpfn_mix_prediction": 1,
            "pyod_autoencoder_score": 0.8,
            "pyod_autoencoder_prediction": 1,
        },
        {
            "SK_ID_CURR": 102,
            "xgboost_score": 0.2,
            "xgboost_prediction": 0,
            "tabpfn_mix_score": 0.2,
            "tabpfn_mix_prediction": 0,
            "pyod_autoencoder_score": 0.2,
            "pyod_autoencoder_prediction": 0,
        },
    ]


def test_wide_prediction_preview_limits_to_first_50_customers(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wide prediction preview caps the web table at 50 unique customers."""
    predictions_dir = Path(deployment_config["paths"]["predictions"])
    predictions_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = predictions_dir / "xgboost_run_1_predictions.parquet"
    prediction_path.write_text("placeholder", encoding="utf-8")

    def fake_read_parquet(path: Path):
        assert path == prediction_path
        return api_services.pd.DataFrame(
            {
                "SK_ID_CURR": list(range(200, 99, -1)),
                "score": [0.1] * 101,
                "prediction": [0] * 101,
                "model_name": ["xgboost"] * 101,
            }
        )

    monkeypatch.setattr(api_services.pd, "read_parquet", fake_read_parquet)

    rows = api_services.wide_prediction_preview(deployment_config, "run_1")

    assert len(rows) == 50
    assert rows[0]["SK_ID_CURR"] == 100
    assert rows[-1]["SK_ID_CURR"] == 149


def test_wide_prediction_preview_allows_missing_models(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wide prediction preview leaves missing model columns empty."""
    predictions_dir = Path(deployment_config["paths"]["predictions"])
    predictions_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = predictions_dir / "xgboost_run_1_predictions.parquet"
    prediction_path.write_text("placeholder", encoding="utf-8")

    def fake_read_parquet(path: Path):
        assert path == prediction_path
        return api_services.pd.DataFrame(
            {
                "SK_ID_CURR": [101],
                "score": [0.2],
                "prediction": [0],
            }
        )

    monkeypatch.setattr(api_services.pd, "read_parquet", fake_read_parquet)

    rows = api_services.wide_prediction_preview(deployment_config, "run_1")

    assert rows == [
        {
            "SK_ID_CURR": 101,
            "xgboost_score": 0.2,
            "xgboost_prediction": 0,
            "tabpfn_mix_score": None,
            "tabpfn_mix_prediction": None,
            "pyod_autoencoder_score": None,
            "pyod_autoencoder_prediction": None,
        }
    ]


def test_model_summaries_include_counts_timings_and_target_metrics(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Model summaries combine manifest, predictions, and TARGET metrics artifacts."""
    _write_api_fixtures(deployment_config)
    prediction_path = Path(deployment_config["paths"]["predictions"]) / "xgboost_run_1_predictions.parquet"

    def fake_read_parquet(path: Path, columns=None):
        assert path == prediction_path
        assert columns == ["prediction"]
        return api_services.pd.DataFrame({"prediction": [0, 1]})

    monkeypatch.setattr(api_services.pd, "read_parquet", fake_read_parquet)

    summaries = api_services.model_summaries(deployment_config, "run_1")

    assert summaries == [
        {
            "model_name": "xgboost",
            "prediction_path": str(prediction_path),
            "metrics_path": str(Path(deployment_config["paths"]["metrics"]) / "xgboost_run_1_predictions_metrics.json"),
            "rows_scored": 2,
            "positive_predictions": 1,
            "negative_predictions": 1,
            "prediction_status": "available",
            "inference_seconds": 1.25,
            "metrics": {
                "holdout_precision": 0.5,
                "holdout_recall": 1.0,
                "holdout_f1": 0.666667,
                "holdout_roc_auc": 0.75,
                "holdout_pr_auc": 0.8,
                "truth_rows_matched": 2,
                "truth_status": "evaluated",
                "rows_per_second": 1.6,
                "avg_latency_ms_per_row": 625.0,
                "deployment_inference_seconds": 1.25,
            },
        }
    ]


def test_resolve_remaps_host_absolute_repo_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Host absolute manifest paths are remapped when the repo is mounted elsewhere."""
    container_root = tmp_path / "work"
    candidate = container_root / "data/ml_outputs/predictions/file.parquet"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("placeholder", encoding="utf-8")
    host_path = Path("/home/alberto/Documents/Github/data-architectures/data/ml_outputs/predictions/file.parquet")

    monkeypatch.setattr(api_services, "REPO_ROOT", container_root)

    assert api_services._resolve(host_path) == candidate


def test_api_inference_endpoint_builds_mocked_command(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inference endpoint delegates to the service without running real scoring."""
    monkeypatch.setattr(api_main, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(
        api_main,
        "run_inference_for_manifest",
        lambda **kwargs: {"returncode": 0, "manifest": kwargs["manifest"], "models": kwargs["models"]},
    )
    response = api_main.api_inference_batch(
        api_main.BatchInferenceRequest(
            manifest="run_1",
            models=["xgboost"],
            skip_clickhouse=True,
        )
    )

    assert response["manifest"] == "run_1"
    assert response["models"] == ["xgboost"]
