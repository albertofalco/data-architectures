"""CLI wrapper for production benchmark runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()

from common.config import load_config
from scoring.benchmark_production import benchmark_production


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Benchmark production batch scoring.")
    parser.add_argument("--model-uri", type=Path, required=True)
    parser.add_argument("--source", choices=["parquet", "clickhouse"], default="clickhouse")
    parser.add_argument("--batch-sizes", default="1,10,100,1000")
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    batch_sizes = [int(value) for value in args.batch_sizes.split(",") if value.strip()]
    output_path = benchmark_production(
        config=load_config(),
        model_uri=args.model_uri,
        batch_sizes=batch_sizes,
        source_name=args.source,
    )
    print(f"Benchmark written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
