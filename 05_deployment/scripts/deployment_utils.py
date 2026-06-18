"""Shared utilities for deployment scripts."""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "05_deployment" / "config" / "deployment.yml"


def resolve_path(path_value: str | Path) -> Path:
    """Resolve a path relative to the repository root."""
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def display_path(path: Path) -> str:
    """Return a repo-relative path when possible, otherwise an absolute path."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_deployment_config(path: Path | None = None) -> dict[str, Any]:
    """Load deployment YAML config."""
    config_path = path or CONFIG_PATH
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def configured_path(config: dict[str, Any], key: str) -> Path:
    """Return a resolved path from deployment config."""
    return resolve_path(config["paths"][key])


def require_path(path: Path, label: str) -> Path:
    """Return an existing path or raise a readable error."""
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    return path


def require_configured_path(config: dict[str, Any], key: str, label: str | None = None) -> Path:
    """Return an existing configured path."""
    return require_path(configured_path(config, key), label or key)


def require_columns(columns: Iterable[str], required: Sequence[str], label: str) -> None:
    """Validate that a tabular object contains required columns."""
    present = set(columns)
    missing = [column for column in required if column not in present]
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")


def require_positive_int(value: int, label: str) -> None:
    """Validate a positive integer argument."""
    if value <= 0:
        raise ValueError(f"{label} must be greater than zero; got {value}")


def require_non_empty(values: Sequence[Any], label: str) -> None:
    """Validate that a sequence is not empty."""
    if not values:
        raise ValueError(f"{label} must not be empty")


def require_unique(values: Sequence[Any], label: str) -> None:
    """Validate that a sequence has no duplicates."""
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        sample = ", ".join(str(value) for value in sorted(duplicates)[:10])
        raise ValueError(f"{label} contains duplicate values: {sample}")


def require_run_id_available(config: dict[str, Any], run_id: str) -> Path:
    """Return the manifest path if the run id is not already used."""
    path = manifest_path(config, run_id)
    if path.exists():
        raise FileExistsError(f"Manifest already exists for run_id '{run_id}': {path}")
    return path


def require_models_exist(config: dict[str, Any], model_names: Sequence[str]) -> dict[str, Path]:
    """Validate that model bundle files exist."""
    require_non_empty(list(model_names), "models")
    models_dir = require_configured_path(config, "models", "models directory")
    model_paths = {}
    missing = []
    for model_name in model_names:
        path = models_dir / f"{model_name}_bundle.joblib"
        if not path.exists():
            missing.append(str(path))
        model_paths[model_name] = path
    if missing:
        raise FileNotFoundError("Missing model bundles: " + ", ".join(missing))
    return model_paths


def ensure_parent(path: Path) -> None:
    """Create a file parent directory."""
    path.parent.mkdir(parents=True, exist_ok=True)


def ensure_dir(path: Path) -> None:
    """Create a directory."""
    path.mkdir(parents=True, exist_ok=True)


def utc_run_id(prefix: str = "prod") -> str:
    """Return a sortable run id."""
    return f"{prefix}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    """Write JSON to disk."""
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def inference_runs_dir(config: dict[str, Any], create: bool = True) -> Path:
    """Return the inference runs directory."""
    path = configured_path(config, "inference_runs")
    if create:
        ensure_dir(path)
    return path


def manifest_path(config: dict[str, Any], run_id: str) -> Path:
    """Return manifest path for a run id."""
    return inference_runs_dir(config) / f"{run_id}.json"


def load_manifest(path_or_run_id: str | Path, config: dict[str, Any]) -> dict[str, Any]:
    """Load a manifest by path or run id."""
    candidate = Path(path_or_run_id)
    if not candidate.suffix:
        candidate = manifest_path(config, str(path_or_run_id))
    if not candidate.is_absolute():
        candidate = resolve_path(candidate)
    return read_json(candidate)


def list_manifests(config: dict[str, Any]) -> list[Path]:
    """List inference manifests."""
    path = inference_runs_dir(config, create=False)
    if not path.exists():
        return []
    return sorted(path.glob("*.json"))


def is_inserted_manifest(manifest: dict[str, Any]) -> bool:
    """Return whether a manifest represents rows inserted into MySQL."""
    return (
        manifest.get("status") == "inserted"
        and int(manifest.get("rows_inserted", 0) or 0) > 0
        and int(manifest.get("holdout_end_rank", 0) or 0) > 0
    )


def inserted_entity_ids(config: dict[str, Any]) -> set[int]:
    """Return entity IDs recorded by inserted manifests."""
    entity_ids: set[int] = set()
    for path in list_manifests(config):
        try:
            manifest = read_json(path)
        except json.JSONDecodeError:
            continue
        if not is_inserted_manifest(manifest):
            continue
        entity_ids.update(int(value) for value in manifest.get("entity_ids", []))
    return entity_ids


def consumed_rank_max(config: dict[str, Any]) -> int:
    """Return the highest holdout rank recorded by inserted manifests."""
    consumed = 0
    for path in list_manifests(config):
        try:
            manifest = read_json(path)
        except json.JSONDecodeError:
            continue
        if not is_inserted_manifest(manifest):
            continue
        consumed = max(consumed, int(manifest.get("holdout_end_rank", 0) or 0))
    return consumed


@contextmanager
def timed() -> Iterator[dict[str, float]]:
    """Measure elapsed seconds into a mutable dict."""
    holder: dict[str, float] = {}
    start = time.perf_counter()
    try:
        yield holder
    finally:
        holder["seconds"] = round(time.perf_counter() - start, 6)


def mysql_engine_from_env(database_required: bool = True):
    """Create a SQLAlchemy MySQL engine from project .env variables."""
    from dotenv import load_dotenv
    from sqlalchemy import create_engine

    load_dotenv(REPO_ROOT / ".env")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME")
    if database_required and not database:
        raise RuntimeError("DB_NAME is required in .env")
    if not user:
        raise RuntimeError("DB_USER is required in .env")
    db_part = f"/{database}" if database else ""
    return create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}:{port}{db_part}")


def clickhouse_client_from_env():
    """Create a clickhouse-connect client from project .env variables."""
    from dotenv import load_dotenv
    import clickhouse_connect

    load_dotenv(REPO_ROOT / ".env")
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    )
