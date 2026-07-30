"""CLI wrapper for production batch scoring."""

# ==================== IMPORTS ====================

from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from _bootstrap import add_src_to_path

add_src_to_path()

from common.config import load_config
from scoring.batch_score import batch_score


# ==================== HELPER FUNCTIONS ====================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for batch scoring."""
    parser = argparse.ArgumentParser(description="Run production-style batch scoring.")
    parser.add_argument("--source", choices=["parquet", "clickhouse"], default="clickhouse")
    parser.add_argument("--model-uri", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--entity-ids-csv", type=Path, default=None)
    parser.add_argument("--entity-id-column", default="SK_ID_CURR")
    parser.add_argument("--output-suffix", default="batch_predictions")
    return parser.parse_args()


# ==================== MAIN FUNCTIONS ====================

def main() -> int:
    """Score a batch, persist its predictions, and return a success code."""
    args = parse_args()
    entity_id_values = None
    if args.entity_ids_csv is not None:
        ids = pd.read_csv(args.entity_ids_csv, usecols=[args.entity_id_column])
        entity_id_values = ids[args.entity_id_column].dropna().tolist()
    output_path = batch_score(
        config=load_config(),
        model_uri=args.model_uri,
        source_name=args.source,
        limit=args.limit,
        entity_id_values=entity_id_values,
        output_suffix=args.output_suffix,
    )
    print(f"Predictions written to {output_path}")
    return 0


# ==================== EXECUTION ====================

if __name__ == "__main__":
    raise SystemExit(main())
