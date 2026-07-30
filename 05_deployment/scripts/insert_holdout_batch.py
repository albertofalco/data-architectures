"""Insert the next ordered holdout batch into MySQL and write a manifest."""

# ==================== IMPORTS ====================

from __future__ import annotations

import argparse
import pandas as pd

from _bootstrap import add_project_paths

add_project_paths()

from deployment_utils import (
    consumed_rank_max,
    display_path,
    inserted_entity_ids,
    load_deployment_config,
    mysql_engine_from_env,
    require_columns,
    require_configured_path,
    require_non_empty,
    require_positive_int,
    require_run_id_available,
    require_unique,
    timed,
    utc_run_id,
    write_json,
)


# ==================== MAIN FUNCTIONS ====================

def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Insert a controlled holdout batch.")
    parser.add_argument("--rows", type=int, default=None, help="Rows to insert.")
    parser.add_argument("--run-id", default=None, help="Explicit run id.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write MySQL or manifest.")
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Write the manifest without inserting into MySQL.",
    )
    return parser.parse_args()


def main() -> int:
    """Select and validate a holdout batch, optionally insert it, and write its manifest."""
    args = parse_args()
    config = load_deployment_config()
    defaults = config.get("defaults", {})
    entity_key = defaults.get("entity_key", "SK_ID_CURR")
    target = defaults.get("target", "TARGET")
    rows_requested = args.rows or int(defaults.get("batch_size", 1000))
    require_positive_int(rows_requested, "rows")
    run_id = args.run_id or utc_run_id(defaults.get("run_id_prefix", "prod"))
    output_path = require_run_id_available(config, run_id)

    holdout_ids_path = require_configured_path(config, "holdout_ids", "holdout IDs asset")
    truth_path = require_configured_path(config, "holdout_truth", "holdout truth asset")
    normalized_path = require_configured_path(config, "normalized_application_train", "normalized application_train source")
    insert_table = config.get("mysql", {}).get("table", defaults.get("insert_table", "application_train"))

    holdout_ids = pd.read_csv(holdout_ids_path)
    require_columns(holdout_ids.columns, ["holdout_rank", entity_key], str(holdout_ids_path))
    require_unique(holdout_ids["holdout_rank"].tolist(), "holdout_rank")
    require_unique(holdout_ids[entity_key].tolist(), entity_key)

    previous_consumed_rank_max = consumed_rank_max(config)
    start_rank = previous_consumed_rank_max + 1
    end_rank = start_rank + rows_requested - 1
    batch_ids = holdout_ids[
        (holdout_ids["holdout_rank"] >= start_rank)
        & (holdout_ids["holdout_rank"] <= end_rank)
    ].copy()

    if batch_ids.empty:
        raise RuntimeError("No holdout IDs remain for insertion.")
    require_unique(batch_ids[entity_key].tolist(), f"selected {entity_key}")
    inserted_ids = inserted_entity_ids(config)
    overlap = sorted(set(int(value) for value in batch_ids[entity_key].tolist()) & inserted_ids)
    if overlap:
        sample = ", ".join(str(value) for value in overlap[:10])
        raise RuntimeError(f"Selected holdout batch overlaps already inserted IDs: {sample}")
    if len(batch_ids) < rows_requested:
        print(f"Warning: requested {rows_requested} rows, found {len(batch_ids)} remaining rows.")

    normalized = pd.read_csv(normalized_path)
    require_columns(normalized.columns, [entity_key], str(normalized_path))
    batch = (
        normalized[normalized[entity_key].isin(set(batch_ids[entity_key]))]
        .sort_values(entity_key)
        .reset_index(drop=True)
    )
    require_non_empty(batch[entity_key].tolist(), "prepared batch")
    require_unique(batch[entity_key].tolist(), f"prepared {entity_key}")
    if len(batch) != len(batch_ids):
        missing = sorted(set(batch_ids[entity_key]) - set(batch[entity_key]))
        sample = ", ".join(str(value) for value in missing[:10])
        raise ValueError(
            f"Normalized source does not contain all selected holdout IDs. "
            f"Missing {len(missing)} values: {sample}"
        )
    if target in batch.columns:
        batch_to_insert = batch.drop(columns=[target])
    else:
        batch_to_insert = batch
    if target in batch_to_insert.columns:
        raise RuntimeError(f"{target} must not be present in the MySQL insert batch.")

    manifest = {
        "run_id": run_id,
        "status": "planned" if args.dry_run else "manifest_only" if args.manifest_only else "inserted",
        "previous_consumed_rank_max": int(previous_consumed_rank_max),
        "holdout_start_rank": int(batch_ids["holdout_rank"].min()),
        "holdout_end_rank": int(batch_ids["holdout_rank"].max()),
        "rows_requested": int(rows_requested),
        "rows_selected": int(len(batch_ids)),
        "rows_prepared": int(len(batch_to_insert)),
        "rows_inserted": 0,
        "sk_id_curr_min": int(batch_ids[entity_key].min()),
        "sk_id_curr_max": int(batch_ids[entity_key].max()),
        "entity_ids": [int(value) for value in batch_ids[entity_key].tolist()],
        "source_ids_path": display_path(holdout_ids_path),
        "truth_path": display_path(truth_path),
        "normalized_source_path": display_path(normalized_path),
        "mysql_table": insert_table,
        "target_removed": target in batch.columns,
    }

    if args.dry_run:
        print(manifest)
        return 0

    if not args.manifest_only:
        with timed() as insert_timer:
            engine = mysql_engine_from_env()
            batch_to_insert.to_sql(insert_table, engine, if_exists="append", index=False, chunksize=1000)
        manifest["rows_inserted"] = int(len(batch_to_insert))
        manifest["mysql_insert_seconds"] = insert_timer["seconds"]

    write_json(output_path, manifest)
    print(f"Manifest written to {output_path}")
    return 0


# ==================== EXECUTION ====================

if __name__ == "__main__":
    raise SystemExit(main())
