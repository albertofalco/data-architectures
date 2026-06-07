"""CLI wrapper for production batch scoring."""

from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()

from common.config import load_config
from scoring.batch_score import batch_score


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run production-style batch scoring.")
    parser.add_argument("--source", choices=["parquet", "clickhouse"], default="clickhouse")
    parser.add_argument("--model-uri", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    output_path = batch_score(
        config=load_config(),
        model_uri=args.model_uri,
        source_name=args.source,
        limit=args.limit,
    )
    print(f"Predictions written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
