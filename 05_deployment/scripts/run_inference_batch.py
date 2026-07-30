"""Run manifest-scoped batch inference using existing ML scoring logic."""

# ==================== IMPORTS ====================

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from _bootstrap import add_project_paths

add_project_paths()

from common.config import load_config as load_ml_config
from deployment_utils import (
    REPO_ROOT,
    clickhouse_client_from_env,
    configured_path,
    load_deployment_config,
    load_manifest,
    manifest_path,
    require_columns,
    require_configured_path,
    require_models_exist,
    require_non_empty,
    require_unique,
    resolve_path,
    timed,
    write_json,
)
from scoring.batch_score import batch_score
from training.evaluate_model import classification_metrics


# ==================== CONFIGURATION ====================

FOUNDATION_DOCKER_MODELS = {"tabpfn_mix", "pyod_autoencoder"}
FOUNDATION_IMAGE = "data-architectures-foundation:py313"


# ==================== HELPER FUNCTIONS ====================

def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run inference for a deployment manifest.")
    parser.add_argument("--manifest", required=True, help="Manifest path or run id.")
    parser.add_argument("--source", choices=["clickhouse", "parquet"], default=None)
    parser.add_argument("--models", default=None, help="Comma-separated model names.")
    parser.add_argument("--skip-clickhouse", action="store_true", help="Do not persist predictions in ClickHouse.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned work without scoring.")
    return parser.parse_args()


def _prediction_rows(
    prediction_path: Path,
    run_id: str,
    metrics_path: Path,
) -> pd.DataFrame:
    """Load prediction parquet and add deployment metadata."""
    predictions = pd.read_parquet(prediction_path)
    predictions["run_id"] = run_id
    predictions["predicted_at"] = datetime.now(UTC).replace(tzinfo=None)
    predictions["prediction_path"] = str(prediction_path)
    predictions["metrics_path"] = str(metrics_path)
    return predictions[
        [
            "run_id",
            "model_name",
            "SK_ID_CURR",
            "score",
            "prediction",
            "predicted_at",
            "prediction_path",
            "metrics_path",
        ]
    ]


def _prediction_path(ml_config: dict, model_name: str, output_suffix: str) -> Path:
    """Return the prediction parquet path written by batch_score."""
    from common.config import configured_path as configured_ml_path

    return configured_ml_path(ml_config, "predictions", "./data/ml_outputs/predictions/") / f"{model_name}_{output_suffix}.parquet"


def _metrics_path(deployment_config: dict, model_name: str, output_suffix: str) -> Path:
    """Return the deployment metrics path for one model run."""
    return configured_path(deployment_config, "metrics") / f"{model_name}_{output_suffix}_metrics.json"


def _write_entity_ids_csv(deployment_config: dict, run_id: str, entity_ids: list[int | str], entity_key: str) -> Path:
    """Write a temporary entity-id CSV consumable by the shared batch_score CLI."""
    runs_dir = configured_path(deployment_config, "inference_runs")
    try:
        runs_dir.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        runs_dir = REPO_ROOT / "data" / "ml_outputs" / "inference_runs"
    path = runs_dir / f".{run_id}_entity_ids.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({entity_key: entity_ids}).to_csv(path, index=False)
    return path


def _container_repo_path(path: Path) -> str:
    """Return a path as seen from the Docker container working at /work."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError as error:
        raise ValueError(f"Docker scoring can only use repo-local paths, got: {path}") from error


def _docker_command(
    model_uri: Path,
    source_name: str,
    entity_ids_csv: Path,
    entity_key: str,
    output_suffix: str,
) -> list[str]:
    """Build the Docker command for foundation/anomaly scoring."""
    command = [
        "docker",
        "run",
        "--rm",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "-v",
        f"{Path.cwd()}:/work",
        "-w",
        "/work",
        "--add-host",
        "host.docker.internal:host-gateway",
    ]
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        command.extend(["--env-file", str(env_file)])
    command.extend(
        [
            "-e",
            "TABPFN_NO_BROWSER=1",
            FOUNDATION_IMAGE,
            "python",
            "04_ml_development/scripts/batch_score.py",
            "--source",
            source_name,
            "--model-uri",
            _container_repo_path(model_uri),
            "--entity-ids-csv",
            _container_repo_path(entity_ids_csv),
            "--entity-id-column",
            entity_key,
            "--output-suffix",
            output_suffix,
        ]
    )
    return command


def _run_docker_batch_score(
    model_uri: Path,
    source_name: str,
    entity_ids: list[int | str],
    entity_key: str,
    deployment_config: dict,
    run_id: str,
    output_suffix: str,
) -> None:
    """Run the shared batch scoring CLI in the foundation Docker image."""
    entity_ids_csv = _write_entity_ids_csv(deployment_config, run_id, entity_ids, entity_key)
    command = _docker_command(
        model_uri=model_uri,
        source_name=source_name,
        entity_ids_csv=entity_ids_csv,
        entity_key=entity_key,
        output_suffix=output_suffix,
    )
    try:
        result = subprocess.run(command, cwd=Path.cwd(), check=False, capture_output=True, text=True)
    finally:
        entity_ids_csv.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Docker foundation scoring failed "
            f"(returncode={result.returncode}). stdout={result.stdout.strip()} stderr={result.stderr.strip()}"
        )


def _run_model_score(
    model_name: str,
    model_uri: Path,
    ml_config: dict,
    deployment_config: dict,
    source_name: str,
    entity_ids: list[int | str],
    entity_key: str,
    run_id: str,
    output_suffix: str,
) -> Path:
    """Score one model using its expected runtime and return prediction path."""
    if model_name in FOUNDATION_DOCKER_MODELS:
        _run_docker_batch_score(
            model_uri=model_uri,
            source_name=source_name,
            entity_ids=entity_ids,
            entity_key=entity_key,
            deployment_config=deployment_config,
            run_id=run_id,
            output_suffix=output_suffix,
        )
        return _prediction_path(ml_config, model_name, output_suffix)
    return batch_score(
        config=ml_config,
        model_uri=model_uri,
        source_name=source_name,
        entity_id_values=entity_ids,
        output_suffix=output_suffix,
    )


def _existing_model_rows(client, database: str, table: str, run_id: str, model_name: str) -> int:
    """Return existing ClickHouse prediction rows for one run/model."""
    rows = client.query(
        f"""
        SELECT count()
        FROM {database}.{table}
        WHERE run_id = %(run_id)s AND model_name = %(model_name)s
        SETTINGS max_execution_time=10, max_result_rows=1
        """,
        parameters={"run_id": run_id, "model_name": model_name},
    ).result_rows
    return int(rows[0][0])


def _persist_model_predictions(
    deployment_config: dict,
    run_id: str,
    model_name: str,
    predictions: pd.DataFrame,
    skip_clickhouse: bool,
) -> str:
    """Persist one model's predictions to ClickHouse when enabled."""
    if skip_clickhouse:
        return "skipped"
    table = deployment_config.get("clickhouse", {}).get("predictions_table", "ml_predictions")
    database = deployment_config.get("clickhouse", {}).get("database", "data_arch_dw")
    client = clickhouse_client_from_env()
    if _existing_model_rows(client, database, table, run_id, model_name) > 0:
        return "already_present"
    client.insert_df(f"{database}.{table}", predictions)
    return "inserted"


def _upsert_model_result(manifest: dict, result: dict) -> None:
    """Upsert one model result into the manifest inference block."""
    inference = manifest.setdefault("inference", {})
    models = inference.setdefault("models", [])
    models[:] = [item for item in models if item.get("model_name") != result.get("model_name")]
    models.append(result)


def _final_status(results: list[dict]) -> str:
    """Return the aggregate inference status from per-model statuses."""
    if not results:
        return "failed"
    statuses = {result.get("status") for result in results}
    if statuses == {"scored"}:
        return "scored"
    if "scored" in statuses:
        return "partial"
    return "failed"


def _add_truth_metrics(
    metrics: dict,
    predictions: pd.DataFrame,
    truth_path: Path,
) -> dict:
    """Add classification metrics when private truth is available."""
    if not truth_path.exists():
        metrics["truth_status"] = "missing"
        return metrics

    truth = pd.read_csv(truth_path)
    evaluation = predictions.merge(truth, on="SK_ID_CURR", how="inner")
    metrics["truth_rows_matched"] = int(len(evaluation))
    if evaluation.empty:
        metrics["truth_status"] = "no_matches"
        return metrics

    metrics.update(
        {
            f"holdout_{name}": value
            for name, value in classification_metrics(
                evaluation["TARGET"],
                evaluation["prediction"],
                evaluation["score"],
            ).items()
        }
    )
    metrics["truth_status"] = "evaluated"
    return metrics


# ==================== MAIN FUNCTIONS ====================

def main() -> int:
    """Score configured models, persist predictions and metrics, and update the manifest."""
    args = parse_args()
    deployment_config = load_deployment_config()
    ml_config = load_ml_config()
    manifest = load_manifest(args.manifest, deployment_config)
    run_id = manifest["run_id"]
    entity_ids = manifest.get("entity_ids", [])
    require_non_empty(entity_ids, "manifest entity_ids")
    require_unique(entity_ids, "manifest entity_ids")

    defaults = deployment_config.get("defaults", {})
    entity_key = defaults.get("entity_key", "SK_ID_CURR")
    target = defaults.get("target", "TARGET")
    source_name = args.source or defaults.get("source_name", "clickhouse")
    models = (
        [item.strip() for item in args.models.split(",") if item.strip()]
        if args.models
        else defaults.get("models", [])
    )
    model_paths = require_models_exist(deployment_config, models)

    truth_path = Path(manifest.get("truth_path", configured_path(deployment_config, "holdout_truth")))
    if not truth_path.is_absolute():
        truth_path = resolve_path(truth_path)
    truth_path = require_configured_path(deployment_config, "holdout_truth", "holdout truth asset") if "truth_path" not in manifest else truth_path
    if not truth_path.exists():
        raise FileNotFoundError(f"holdout truth asset does not exist: {truth_path}")
    truth = pd.read_csv(truth_path, nrows=0)
    require_columns(truth.columns, [entity_key, target], str(truth_path))

    if args.dry_run:
        print(
            {
                "run_id": run_id,
                "source": source_name,
                "models": models,
                "model_paths": {name: str(path) for name, path in model_paths.items()},
                "truth_path": str(truth_path),
                "entity_count": len(entity_ids),
                "clickhouse_persist": not args.skip_clickhouse,
            }
        )
        return 0

    inference_results = list(manifest.get("inference", {}).get("models", []))
    manifest.setdefault("inference", {})
    manifest["inference"].setdefault("models", inference_results)

    for model_name in models:
        model_uri = model_paths[model_name]
        output_suffix = f"{run_id}_predictions"
        metrics_path = _metrics_path(deployment_config, model_name, output_suffix)
        try:
            with timed() as model_timer:
                prediction_path = _run_model_score(
                    model_name=model_name,
                    model_uri=model_uri,
                    ml_config=ml_config,
                    deployment_config=deployment_config,
                    source_name=source_name,
                    entity_ids=entity_ids,
                    entity_key=entity_key,
                    run_id=run_id,
                    output_suffix=output_suffix,
                )

            predictions = _prediction_rows(prediction_path, run_id=run_id, metrics_path=metrics_path)
            metrics = {}
            if metrics_path.exists():
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            metrics["deployment_inference_seconds"] = model_timer["seconds"]
            metrics = _add_truth_metrics(metrics, predictions, truth_path)
            write_json(metrics_path, metrics)
            clickhouse_status = _persist_model_predictions(
                deployment_config=deployment_config,
                run_id=run_id,
                model_name=model_name,
                predictions=predictions,
                skip_clickhouse=args.skip_clickhouse,
            )
            result = {
                "model_name": model_name,
                "status": "scored",
                "runtime": "docker_foundation" if model_name in FOUNDATION_DOCKER_MODELS else "local",
                "model_uri": str(model_uri),
                "prediction_path": str(prediction_path),
                "metrics_path": str(metrics_path),
                "rows_scored": int(len(predictions)),
                "inference_seconds": model_timer["seconds"],
                "clickhouse_status": clickhouse_status,
            }
        except Exception as error:
            result = {
                "model_name": model_name,
                "status": "failed",
                "runtime": "docker_foundation" if model_name in FOUNDATION_DOCKER_MODELS else "local",
                "model_uri": str(model_uri),
                "metrics_path": str(metrics_path),
                "error": str(error),
            }
            print(f"Model {model_name} failed: {error}")

        _upsert_model_result(manifest, result)
        inference_results = manifest["inference"]["models"]
        manifest["inference"].update(
            {
                "status": _final_status(inference_results),
                "source": source_name,
                "clickhouse_persisted": any(
                    item.get("clickhouse_status") in {"inserted", "already_present"}
                    for item in inference_results
                ),
            }
        )
        write_json(manifest_path(deployment_config, run_id), manifest)

    write_json(manifest_path(deployment_config, run_id), manifest)
    print(f"Inference recorded for run {run_id}")
    return 0 if any(result.get("status") == "scored" for result in inference_results) else 1


# ==================== EXECUTION ====================

if __name__ == "__main__":
    raise SystemExit(main())
