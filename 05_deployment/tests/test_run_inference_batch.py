"""Tests for manifest-scoped inference orchestration."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

from conftest import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_inference_inputs(config: dict, run_id: str = "run_1") -> Path:
    """Create model, truth, and manifest fixtures."""
    models_dir = Path(config["paths"]["models"])
    truth_path = Path(config["paths"]["holdout_truth"])
    runs_dir = Path(config["paths"]["inference_runs"])
    models_dir.mkdir(parents=True, exist_ok=True)
    truth_path.parent.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)

    (models_dir / "xgboost_bundle.joblib").write_bytes(b"test bundle placeholder")
    pd.DataFrame({"SK_ID_CURR": [101, 102], "TARGET": [0, 1]}).to_csv(truth_path, index=False)
    manifest_path = runs_dir / f"{run_id}.json"
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "entity_ids": [101, 102],
                "truth_path": str(truth_path),
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_dry_run_validates_inputs_without_scoring(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dry-run reports planned work and does not call the scorer."""
    _write_inference_inputs(deployment_config)
    module = load_script_module("run_inference_batch")
    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(module, "load_ml_config", lambda: {"ml_pipeline": {"entity_key": "SK_ID_CURR"}})
    monkeypatch.setattr(module, "batch_score", lambda **_: pytest.fail("batch_score should not run"))
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_inference_batch.py", "--manifest", "run_1", "--models", "xgboost", "--dry-run"],
    )

    assert module.main() == 0

    payload = ast.literal_eval(capsys.readouterr().out.strip())
    assert payload["run_id"] == "run_1"
    assert payload["models"] == ["xgboost"]
    assert payload["entity_count"] == 2
    assert payload["clickhouse_persist"] is True


def test_missing_model_bundle_is_rejected(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Configured models must have bundle artifacts before inference."""
    _write_inference_inputs(deployment_config)
    (Path(deployment_config["paths"]["models"]) / "xgboost_bundle.joblib").unlink()
    module = load_script_module("run_inference_batch")
    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(module, "load_ml_config", lambda: {})
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_inference_batch.py", "--manifest", "run_1", "--models", "xgboost", "--dry-run"],
    )

    with pytest.raises(FileNotFoundError, match="Missing model bundles"):
        module.main()


def test_scoring_continues_after_model_failure(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failing model records failure without discarding a previous success."""
    _write_inference_inputs(deployment_config)
    models_dir = Path(deployment_config["paths"]["models"])
    (models_dir / "bad_model_bundle.joblib").write_bytes(b"placeholder")
    deployment_config["defaults"]["models"] = ["xgboost", "bad_model"]
    module = load_script_module("run_inference_batch")
    prediction_path = Path(deployment_config["paths"]["predictions"]) / "xgboost_run_1_predictions.parquet"
    prediction_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "SK_ID_CURR": [101, 102],
            "score": [0.1, 0.9],
            "prediction": [0, 1],
            "model_name": ["xgboost", "xgboost"],
        }
    ).to_parquet(prediction_path, index=False)

    def fake_score(**kwargs):
        if kwargs["model_uri"].name.startswith("bad_model"):
            raise RuntimeError("boom")
        return prediction_path

    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(module, "load_ml_config", lambda: {"ml_pipeline": {"entity_key": "SK_ID_CURR"}})
    monkeypatch.setattr(module, "batch_score", fake_score)
    monkeypatch.setattr(module, "_persist_model_predictions", lambda **_: "skipped")
    monkeypatch.setattr(sys, "argv", ["run_inference_batch.py", "--manifest", "run_1"])

    assert module.main() == 0

    manifest = json.loads((Path(deployment_config["paths"]["inference_runs"]) / "run_1.json").read_text())
    results = {item["model_name"]: item for item in manifest["inference"]["models"]}
    assert manifest["inference"]["status"] == "partial"
    assert results["xgboost"]["status"] == "scored"
    assert results["bad_model"]["status"] == "failed"


def test_foundation_models_use_docker_batch_score(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Foundation/anomaly models delegate scoring to the shared Docker runtime."""
    module = load_script_module("run_inference_batch")
    commands = []

    class Result:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(command, cwd, check, capture_output, text):
        commands.append(command)
        return Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module._run_docker_batch_score(
        model_uri=Path("data/ml_outputs/models/tabpfn_mix_bundle.joblib"),
        source_name="clickhouse",
        entity_ids=[101, 102],
        entity_key="SK_ID_CURR",
        deployment_config=deployment_config,
        run_id="run_1",
        output_suffix="run_1_predictions",
    )

    command = commands[0]
    assert command[:3] == ["docker", "run", "--rm"]
    assert "data-architectures-foundation:py313" in command
    assert "04_ml_development/scripts/batch_score.py" in command
    assert "--entity-ids-csv" in command
    assert not (Path(deployment_config["paths"]["inference_runs"]) / ".run_1_entity_ids.csv").exists()


def test_foundation_requirements_include_clickhouse_client() -> None:
    """The foundation runtime must support ClickHouse-backed batch scoring."""
    requirements = (
        REPO_ROOT / "04_ml_development" / "requirements-foundation-py313.txt"
    ).read_text(encoding="utf-8")

    assert "clickhouse-connect==" in requirements
