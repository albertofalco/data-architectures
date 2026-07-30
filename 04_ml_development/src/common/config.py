"""Configuration and path helpers for ML development scripts."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# ==================== CONFIGURATION ====================

MODULE_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = MODULE_DIR.parent
CONFIG_PATH = MODULE_DIR / "config.yml"


# ==================== HELPER FUNCTIONS ====================

def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load the ML development YAML configuration."""
    path = config_path or CONFIG_PATH
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def resolve_project_path(path_value: str | Path) -> Path:
    """Resolve a config path relative to the repository root."""
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (BASE_DIR / path).resolve()


def configured_path(config: dict[str, Any], key: str, default: str) -> Path:
    """Return a configured path from the `paths` section or a default."""
    paths = config.get("paths", {})
    return resolve_project_path(paths.get(key, default))


def normalize_table_name(table: str) -> str:
    """Normalize a table argument to its parquet stem."""
    return Path(table).stem


def find_parquet_files(data_dir: Path, tables: list[str] | None = None) -> tuple[list[Path], list[str]]:
    """Return matching parquet files and requested table names not found."""
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    available = {path.stem: path for path in sorted(data_dir.glob("*.parquet"))}
    if not tables:
        return list(available.values()), []

    selected: list[Path] = []
    missing: list[str] = []
    for table in tables:
        name = normalize_table_name(table)
        path = available.get(name)
        if path is None:
            missing.append(table)
        else:
            selected.append(path)
    return selected, missing
