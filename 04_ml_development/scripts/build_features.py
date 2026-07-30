"""CLI wrapper for engineered feature generation."""

# ==================== IMPORTS ====================

from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()

from common.config import load_config
from data_engineering.build_features import build_features


# ==================== HELPER FUNCTIONS ====================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for feature generation."""
    parser = argparse.ArgumentParser(description="Build model features.")
    parser.add_argument("--source", choices=["parquet", "clickhouse"], default="parquet")
    parser.add_argument("--output-path", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


# ==================== MAIN FUNCTIONS ====================

def main() -> int:
    """Build and persist model features, then return a success code."""
    args = parse_args()
    output_path = build_features(
        config=load_config(),
        source_name=args.source,
        output_path=args.output_path,
        limit=args.limit,
    )
    print(f"Features written to {output_path}")
    return 0


# ==================== EXECUTION ====================

if __name__ == "__main__":
    raise SystemExit(main())
