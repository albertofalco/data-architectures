"""Measure local artifact storage and optionally database storage footprints."""

# ==================== IMPORTS ====================

from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import add_project_paths

add_project_paths()

from deployment_utils import (
    clickhouse_client_from_env,
    configured_path,
    load_deployment_config,
    mysql_engine_from_env,
    timed,
    utc_run_id,
    write_json,
)


# ==================== HELPER FUNCTIONS ====================

def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Measure deployment storage footprint.")
    parser.add_argument("--run-id", default=None, help="Run id for output filename.")
    parser.add_argument(
        "--include-databases",
        action="store_true",
        help="Query MySQL and ClickHouse system tables.",
    )
    return parser.parse_args()


def _path_size(path: Path) -> int:
    """Return path size in bytes."""
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _local_storage(config: dict) -> dict:
    """Measure configured local paths."""
    keys = [
        "holdout_ids",
        "holdout_truth",
        "inference_runs",
        "predictions",
        "metrics",
        "models",
    ]
    rows = {}
    for key in keys:
        path = configured_path(config, key)
        size = _path_size(path)
        rows[key] = {
            "path": str(path),
            "exists": path.exists(),
            "bytes": size,
            "mb": round(size / 1024**2, 6),
        }
    return rows


def _database_storage(config: dict) -> dict:
    """Measure database storage using metadata queries."""
    results = {}
    with timed() as mysql_timer:
        engine = mysql_engine_from_env()
        query = """
        SELECT table_schema, table_name, data_length + index_length AS bytes
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        """
        import pandas as pd

        mysql_rows = pd.read_sql(query, engine).to_dict(orient="records")
    results["mysql"] = {"seconds": mysql_timer["seconds"], "tables": mysql_rows}

    with timed() as clickhouse_timer:
        database = config.get("clickhouse", {}).get("database", "data_arch_dw")
        client = clickhouse_client_from_env()
        ch_rows = client.query(
            f"""
            SELECT database, table, sum(bytes_on_disk) AS bytes, sum(rows) AS rows
            FROM system.parts
            WHERE active AND database IN ('{database}', '{config.get("clickhouse", {}).get("staging_database", "staging_mysql")}')
            GROUP BY database, table
            ORDER BY database, table
            """
        ).result_rows
    results["clickhouse"] = {
        "seconds": clickhouse_timer["seconds"],
        "tables": [
            {"database": row[0], "table": row[1], "bytes": int(row[2]), "rows": int(row[3])}
            for row in ch_rows
        ],
    }
    return results


# ==================== MAIN FUNCTIONS ====================

def main() -> int:
    """Measure storage footprint and write a JSON report."""
    args = parse_args()
    config = load_deployment_config()
    run_id = args.run_id or utc_run_id("storage")
    payload = {
        "run_id": run_id,
        "local": _local_storage(config),
        "database_storage_included": args.include_databases,
    }
    if args.include_databases:
        payload["databases"] = _database_storage(config)

    output_path = configured_path(config, "metrics") / f"{run_id}_storage_metrics.json"
    write_json(output_path, payload)
    print(f"Storage metrics written to {output_path}")
    return 0


# ==================== EXECUTION ====================

if __name__ == "__main__":
    raise SystemExit(main())
