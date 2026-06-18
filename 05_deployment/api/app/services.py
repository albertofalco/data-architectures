"""Service helpers for the deployment API."""

from __future__ import annotations

import subprocess
import sys
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
DEPLOYMENT_CONFIG = REPO_ROOT / "05_deployment" / "config" / "deployment.yml"
PREDICTION_DISPLAY_MODELS = ("xgboost", "tabpfn_mix", "pyod_autoencoder")


class DeploymentAPIError(RuntimeError):
    """Base error for readable API failures."""


class PredictionReadError(DeploymentAPIError):
    """Raised when local prediction files cannot be read."""


def _resolve(path_value: str | Path) -> Path:
    """Resolve a path relative to repository root."""
    path = Path(path_value).expanduser()
    if path.is_absolute():
        if path.exists():
            return path
        if REPO_ROOT.name in path.parts:
            repo_index = len(path.parts) - 1 - list(reversed(path.parts)).index(REPO_ROOT.name)
            candidate = REPO_ROOT.joinpath(*path.parts[repo_index + 1 :])
            if candidate.exists():
                return candidate
        for marker in ("data", "05_deployment", "04_ml_development", "docs"):
            if marker in path.parts:
                marker_index = path.parts.index(marker)
                candidate = REPO_ROOT.joinpath(*path.parts[marker_index:])
                if candidate.exists():
                    return candidate
        return path
    return (REPO_ROOT / path).resolve()


def load_deployment_config() -> dict[str, Any]:
    """Load deployment configuration."""
    try:
        with DEPLOYMENT_CONFIG.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}
    except OSError as error:
        raise DeploymentAPIError(f"Deployment config cannot be read: {DEPLOYMENT_CONFIG}") from error


def _configured_path(config: dict[str, Any], key: str) -> Path:
    """Resolve a configured deployment path."""
    return _resolve(config["paths"][key])


def _manifest_paths(config: dict[str, Any]) -> list[Path]:
    """Return manifest paths."""
    runs_dir = _configured_path(config, "inference_runs")
    if not runs_dir.exists():
        return []
    return sorted(runs_dir.glob("*.json"), reverse=True)


def load_run(config: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Load one run manifest."""
    path = _configured_path(config, "inference_runs") / f"{run_id}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise DeploymentAPIError(f"Run manifest is not valid JSON: {path}") from error


def list_runs(config: dict[str, Any]) -> list[dict[str, Any]]:
    """List compact run summaries."""
    rows = []
    for path in _manifest_paths(config):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        rows.append(
            {
                "run_id": manifest.get("run_id", path.stem),
                "status": manifest.get("status", "unknown"),
                "rows_selected": manifest.get("rows_selected"),
                "rows_inserted": manifest.get("rows_inserted"),
                "sk_id_curr_min": manifest.get("sk_id_curr_min"),
                "sk_id_curr_max": manifest.get("sk_id_curr_max"),
                "inference_status": manifest.get("inference", {}).get("status"),
            }
        )
    return rows


def list_predictions(
    config: dict[str, Any],
    run_id: str | None = None,
    model_name: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Read local prediction parquet files and return rows."""
    predictions_dir = _configured_path(config, "predictions")
    if not predictions_dir.exists():
        return []

    frames = []
    for path in sorted(predictions_dir.glob("*.parquet"), reverse=True):
        if run_id and run_id not in path.name:
            continue
        if model_name and not path.name.startswith(f"{model_name}_"):
            continue
        try:
            frame = pd.read_parquet(path)
        except Exception as error:
            raise PredictionReadError(f"Prediction file cannot be read: {path}") from error
        if "run_id" not in frame.columns and run_id:
            frame["run_id"] = run_id
        frames.append(frame)
        if sum(len(item) for item in frames) >= limit:
            break

    if not frames:
        return []
    combined = pd.concat(frames, ignore_index=True).head(limit)
    return combined.to_dict(orient="records")


def _model_name_from_prediction_path(path: Path, run_id: str) -> str:
    """Infer the model name from a deployment prediction artifact name."""
    suffix = f"_{run_id}_predictions"
    if path.stem.endswith(suffix):
        return path.stem[: -len(suffix)]
    return path.stem.split("_", 1)[0]


def wide_prediction_preview(
    config: dict[str, Any],
    run_id: str,
    limit: int = 50,
    models: tuple[str, ...] = PREDICTION_DISPLAY_MODELS,
) -> list[dict[str, Any]]:
    """Return a one-row-per-customer prediction preview for the web UI."""
    predictions_dir = _configured_path(config, "predictions")
    if not predictions_dir.exists():
        return []

    frames = []
    required_columns = ["SK_ID_CURR", "score", "prediction"]
    for path in sorted(predictions_dir.glob("*.parquet")):
        if run_id not in path.name:
            continue
        try:
            frame = pd.read_parquet(path)
        except Exception as error:
            raise PredictionReadError(f"Prediction file cannot be read: {path}") from error
        if not set(required_columns).issubset(frame.columns):
            continue
        if "model_name" not in frame.columns:
            frame["model_name"] = _model_name_from_prediction_path(path, run_id)
        frame = frame[["SK_ID_CURR", "model_name", "score", "prediction"]]
        frame = frame[frame["model_name"].isin(models)]
        if not frame.empty:
            frames.append(frame)

    if not frames:
        return []

    combined = pd.concat(frames, ignore_index=True)
    entity_ids = sorted(combined["SK_ID_CURR"].dropna().unique())[:limit]
    combined = combined[combined["SK_ID_CURR"].isin(entity_ids)]

    rows_by_entity: dict[Any, dict[str, Any]] = {
        entity_id: {
            "SK_ID_CURR": entity_id,
            **{
                key: None
                for model in models
                for key in (f"{model}_score", f"{model}_prediction")
            },
        }
        for entity_id in entity_ids
    }
    for row in combined.sort_values(["SK_ID_CURR", "model_name"]).to_dict(orient="records"):
        entity_id = row["SK_ID_CURR"]
        model = row["model_name"]
        if entity_id not in rows_by_entity or model not in models:
            continue
        rows_by_entity[entity_id][f"{model}_score"] = row["score"]
        rows_by_entity[entity_id][f"{model}_prediction"] = row["prediction"]

    return [rows_by_entity[entity_id] for entity_id in entity_ids]


def _read_json_file(path: Path) -> dict[str, Any]:
    """Read a JSON file and return an empty dict when it is absent."""
    if not str(path) or not path.exists() or path.is_dir():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise DeploymentAPIError(f"JSON artifact is not valid: {path}") from error


def _prediction_counts(path: Path) -> dict[str, int | str]:
    """Return positive/negative prediction counts for one prediction artifact."""
    if not str(path) or not path.exists() or path.is_dir():
        return {
            "prediction_status": "missing",
            "rows_scored": 0,
            "positive_predictions": 0,
            "negative_predictions": 0,
        }
    try:
        frame = pd.read_parquet(path, columns=["prediction"])
    except Exception as error:
        raise PredictionReadError(f"Prediction file cannot be read: {path}") from error

    counts = frame["prediction"].value_counts(dropna=False).to_dict()
    positives = int(counts.get(1, 0))
    negatives = int(counts.get(0, 0))
    return {
        "prediction_status": "available",
        "rows_scored": int(len(frame)),
        "positive_predictions": positives,
        "negative_predictions": negatives,
    }


def _model_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """Extract display metrics from a model metrics artifact."""
    metric_names = [
        "holdout_precision",
        "holdout_recall",
        "holdout_f1",
        "holdout_roc_auc",
        "holdout_pr_auc",
        "truth_rows_matched",
        "truth_status",
        "production_extract_transform_seconds",
        "production_transform_seconds",
        "production_predict_seconds",
        "production_total_seconds",
        "rows_per_second",
        "avg_latency_ms_per_row",
        "deployment_inference_seconds",
    ]
    return {name: metrics[name] for name in metric_names if name in metrics}


def model_summaries(config: dict[str, Any], run_id: str) -> list[dict[str, Any]]:
    """Return per-model prediction counts, timings, and TARGET metrics for a run."""
    run = load_run(config, run_id)
    summaries = []
    for model in run.get("inference", {}).get("models", []):
        model_name = model.get("model_name", "unknown")
        prediction_path_value = model.get("prediction_path")
        metrics_path_value = model.get("metrics_path")
        prediction_path = _resolve(prediction_path_value) if prediction_path_value else Path()
        metrics_path = _resolve(metrics_path_value) if metrics_path_value else Path()
        metrics = _read_json_file(metrics_path)
        counts = _prediction_counts(prediction_path)
        rows_scored = int(model.get("rows_scored") or counts["rows_scored"])
        seconds = model.get("inference_seconds") or metrics.get("deployment_inference_seconds")
        summaries.append(
            {
                "model_name": model_name,
                "prediction_path": str(prediction_path),
                "metrics_path": str(metrics_path),
                "rows_scored": rows_scored,
                "positive_predictions": counts["positive_predictions"],
                "negative_predictions": counts["negative_predictions"],
                "prediction_status": counts["prediction_status"],
                "inference_seconds": seconds,
                "metrics": _model_metrics(metrics),
            }
        )
    return summaries


def run_inference_for_manifest(
    config: dict[str, Any],
    manifest: str,
    source: str | None,
    models: list[str] | None,
    skip_clickhouse: bool,
) -> dict[str, Any]:
    """Invoke the deployment inference script."""
    command = [
        sys.executable,
        str(REPO_ROOT / "05_deployment" / "scripts" / "run_inference_batch.py"),
        "--manifest",
        manifest,
    ]
    if source:
        command.extend(["--source", source])
    if models:
        command.extend(["--models", ",".join(models)])
    if skip_clickhouse:
        command.append("--skip-clickhouse")

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": command,
    }
