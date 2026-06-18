"""Generate immutable holdout assets for production inference simulation."""

from __future__ import annotations

import argparse

import pandas as pd

from _bootstrap import add_project_paths

add_project_paths()

from deployment_utils import configured_path, ensure_parent, load_deployment_config


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Generate holdout ID and truth assets.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing assets.")
    return parser.parse_args()


def main() -> int:
    """Generate holdout assets from raw application_train minus DW application_train."""
    args = parse_args()
    config = load_deployment_config()
    entity_key = config.get("defaults", {}).get("entity_key", "SK_ID_CURR")
    target = config.get("defaults", {}).get("target", "TARGET")

    raw_path = configured_path(config, "raw_application_train")
    dw_path = configured_path(config, "dw_application_train")
    ids_path = configured_path(config, "holdout_ids")
    truth_path = configured_path(config, "holdout_truth")

    if (ids_path.exists() or truth_path.exists()) and not args.overwrite:
        raise FileExistsError(
            "Holdout assets already exist. Pass --overwrite to regenerate them."
        )

    raw = pd.read_csv(raw_path, usecols=[entity_key, target])
    dw_ids = pd.read_parquet(dw_path, columns=[entity_key])[entity_key]

    holdout = (
        raw.loc[~raw[entity_key].isin(set(dw_ids)), [entity_key, target]]
        .drop_duplicates(subset=[entity_key])
        .sort_values(entity_key)
        .reset_index(drop=True)
    )
    holdout_ids = pd.DataFrame(
        {
            "holdout_rank": range(1, len(holdout) + 1),
            entity_key: holdout[entity_key],
        }
    )
    truth = holdout[[entity_key, target]]

    ensure_parent(ids_path)
    holdout_ids.to_csv(ids_path, index=False)
    truth.to_csv(truth_path, index=False)

    print(f"Holdout IDs written to {ids_path} ({len(holdout_ids)} rows)")
    print(f"Holdout truth written to {truth_path} ({len(truth)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
