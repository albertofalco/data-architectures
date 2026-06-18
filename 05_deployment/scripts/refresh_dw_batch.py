"""Refresh ClickHouse storage/reporting for a manifest-scoped application batch."""

from __future__ import annotations

import argparse
import json

from _bootstrap import add_project_paths

add_project_paths()

from deployment_utils import (
    clickhouse_client_from_env,
    load_deployment_config,
    load_manifest,
    require_non_empty,
    require_unique,
    timed,
    write_json,
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Refresh DW rows for a holdout manifest.")
    parser.add_argument("--manifest", required=True, help="Manifest path or run id.")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without executing it.")
    return parser.parse_args()


def _format_ids(entity_ids: list[int | str]) -> str:
    """Format entity ids for a ClickHouse IN clause."""
    return ", ".join(str(int(value)) for value in entity_ids)


def _insert_sql(database: str, staging_db: str, table: str, entity_key: str, entity_ids: list[int | str]) -> str:
    """Build the manifest-scoped storage insert statement."""
    return f"""
    INSERT INTO {database}.{table}
    SELECT *
    FROM {staging_db}.{table}
    WHERE {entity_key} IN ({_format_ids(entity_ids)})
    """.strip()


def _count_sql(database: str, table: str, entity_key: str, entity_ids: list[int | str]) -> str:
    """Build a manifest-scoped count query."""
    return f"""
    SELECT count()
    FROM {database}.{table}
    WHERE {entity_key} IN ({_format_ids(entity_ids)})
    """.strip()


def _duplicate_sql(database: str, table: str, entity_key: str, entity_ids: list[int | str]) -> str:
    """Build a preflight duplicate check query."""
    return f"""
    SELECT {entity_key}, count() AS rows
    FROM {database}.{table}
    WHERE {entity_key} IN ({_format_ids(entity_ids)})
    GROUP BY {entity_key}
    HAVING rows > 0
    ORDER BY {entity_key}
    """.strip()


def main() -> int:
    """Insert manifest-scoped rows from staging into ClickHouse storage."""
    args = parse_args()
    config = load_deployment_config()
    manifest = load_manifest(args.manifest, config)
    entity_ids = manifest.get("entity_ids", [])
    require_non_empty(entity_ids, "manifest entity_ids")
    require_unique(entity_ids, "manifest entity_ids")

    ch_config = config.get("clickhouse", {})
    staging_db = ch_config.get("staging_database", "staging_mysql")
    database = ch_config.get("database", "data_arch_dw")
    table = config.get("defaults", {}).get("insert_table", "application_train")
    entity_key = config.get("defaults", {}).get("entity_key", "SK_ID_CURR")

    sql = _insert_sql(database, staging_db, table, entity_key, entity_ids)
    duplicate_sql = _duplicate_sql(database, table, entity_key, entity_ids)
    storage_count_sql = _count_sql(database, table, entity_key, entity_ids)
    reporting_count_sql = _count_sql(database, f"rep_{table}", entity_key, entity_ids)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "run_id": manifest.get("run_id"),
                    "entity_count": len(entity_ids),
                    "insert_sql": sql,
                    "preflight_duplicate_sql": duplicate_sql,
                    "post_refresh_storage_count_sql": storage_count_sql,
                    "post_refresh_reporting_count_sql": reporting_count_sql,
                    "note": "Dry-run only; no ClickHouse connection or inserts are executed.",
                },
                indent=2,
            )
        )
        return 0

    with timed() as refresh_timer:
        client = clickhouse_client_from_env()
        duplicates = client.query(duplicate_sql).result_rows
        if duplicates:
            sample = ", ".join(str(row[0]) for row in duplicates[:10])
            raise RuntimeError(f"Storage table already contains selected IDs: {sample}")
        client.command(sql)
        storage_count = client.query(storage_count_sql).result_rows[0][0]
        reporting_count = client.query(reporting_count_sql).result_rows[0][0]

    manifest.setdefault("dw_refresh", {})
    manifest["dw_refresh"].update(
        {
            "status": "refreshed",
            "storage_table": f"{database}.{table}",
            "staging_table": f"{staging_db}.{table}",
            "entity_count": len(entity_ids),
            "storage_count": int(storage_count),
            "reporting_count": int(reporting_count),
            "refresh_seconds": refresh_timer["seconds"],
            "note": "Incremental materialized views should populate rep_application_train. If reporting_count is lower than entity_count, run a manifest-scoped reporting backfill before scoring.",
        }
    )
    write_json(load_manifest_path(args.manifest, config), manifest)
    print(f"DW refresh recorded for run {manifest['run_id']}")
    return 0


def load_manifest_path(path_or_run_id: str, config: dict) -> object:
    """Resolve manifest path after loading by path or run id."""
    from pathlib import Path
    from deployment_utils import manifest_path, resolve_path

    candidate = Path(path_or_run_id)
    if not candidate.suffix:
        return manifest_path(config, path_or_run_id)
    if not candidate.is_absolute():
        return resolve_path(candidate)
    return candidate


if __name__ == "__main__":
    raise SystemExit(main())
