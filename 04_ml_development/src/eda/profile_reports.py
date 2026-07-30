"""HTML profile report generation for local DW parquet files."""

# ==================== IMPORTS ====================

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd
import pyarrow.parquet as pq

from common.config import configured_path, find_parquet_files, load_config


# ==================== CONFIGURATION ====================

DEFAULT_SAMPLE_SIZE = 100_000
DEFAULT_RANDOM_STATE = 42


# ==================== HELPER FUNCTIONS ====================

def python_compatibility_note() -> str:
    """Return installation guidance for unsupported Python versions."""
    if sys.version_info < (3, 14):
        return ""

    return (
        " fg-data-profiling lists a Python 3.14 classifier, but its "
        "installable package metadata currently requires Python <3.14; "
        "use a Python 3.13 or lower virtualenv for this script until "
        "upstream updates Requires-Python."
    )


def load_profile_report_class() -> Any:
    """Import and return the profiling class with actionable errors."""
    try:
        from data_profiling import ProfileReport
    except ImportError as error:
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        compatibility_note = python_compatibility_note()

        if importlib.util.find_spec("data_profiling") is None:
            raise RuntimeError(
                "Missing dependency fg-data-profiling. Install "
                "`04_ml_development/requirements.txt` in the active virtualenv. "
                f"Current Python: {python_version}.{compatibility_note}"
            ) from error

        raise RuntimeError(
            "Could not import fg-data-profiling after locating `data_profiling`. "
            f"Original error: {error}. Current Python: {python_version}.{compatibility_note}"
        ) from error

    return ProfileReport


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for profile report generation."""
    parser = argparse.ArgumentParser(
        description="Generate fg-data-profiling HTML reports for DW parquet files."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory containing parquet files. Defaults to paths.dw_data in config.yml.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for HTML reports. Defaults to paths.profile_reports in config.yml.",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=None,
        help="Optional parquet table stems or filenames to profile.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help=f"Rows to sample per table unless --full is used. Default: {DEFAULT_SAMPLE_SIZE}.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Profile the full parquet file instead of a reproducible sample.",
    )
    parser.add_argument(
        "--minimal",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use fg-data-profiling minimal mode. Enabled by default.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=DEFAULT_RANDOM_STATE,
        help="Random seed used for reproducible sampling.",
    )
    return parser.parse_args()


def read_profile_dataframe(path: Path, full: bool, sample_size: int, random_state: int) -> pd.DataFrame:
    """Read a full parquet file or build a reproducible bounded sample."""
    parquet_file = pq.ParquetFile(path)
    total_rows = parquet_file.metadata.num_rows

    if full or total_rows <= sample_size:
        return pd.read_parquet(path)

    sampled: pd.DataFrame | None = None
    seen_rows = 0

    for batch_number, batch in enumerate(parquet_file.iter_batches(batch_size=100_000)):
        batch_df = batch.to_pandas()
        seen_rows += len(batch_df)
        if sampled is None:
            sampled = batch_df
        else:
            sampled = pd.concat([sampled, batch_df], ignore_index=True)

        if len(sampled) > sample_size:
            sampled = sampled.sample(
                n=sample_size,
                random_state=random_state + batch_number,
                ignore_index=True,
            )

    if sampled is None:
        return pd.DataFrame()

    if len(sampled) > sample_size:
        sampled = sampled.sample(n=sample_size, random_state=random_state, ignore_index=True)

    print(f"Sampled {len(sampled):,} of {seen_rows:,} rows from {path.name}")
    return sampled


def generate_report(
    path: Path,
    output_dir: Path,
    full: bool,
    sample_size: int,
    minimal: bool,
    random_state: int,
    profile_report_cls: Any,
) -> Path:
    """Generate and persist one HTML profile report."""
    print(f"Generating profile for {path.name}")
    df = read_profile_dataframe(
        path=path,
        full=full,
        sample_size=sample_size,
        random_state=random_state,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{path.stem}_profile_report.html"
    profile = profile_report_cls(
        df,
        title=f"Informe de Perfilado: {path.stem}",
        minimal=minimal,
    )
    profile.to_file(output_path)
    return output_path


# ==================== MAIN FUNCTIONS ====================

def main() -> int:
    """Generate reports for the selected tables and return an exit code."""
    args = parse_args()
    if args.sample_size <= 0:
        print("--sample-size must be greater than zero.", file=sys.stderr)
        return 1

    config = load_config()
    data_dir = args.data_dir or configured_path(config, "dw_data", "./data/dw_parquet/")
    output_dir = args.output_dir or configured_path(
        config, "profile_reports", "./data/ml_outputs/profile_reports/"
    )

    try:
        files, missing = find_parquet_files(data_dir, args.tables)
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 1

    if missing:
        print(f"Missing tables: {', '.join(missing)}", file=sys.stderr)

    if not files:
        print(f"No parquet files found in {data_dir}", file=sys.stderr)
        return 1

    try:
        profile_report_cls = load_profile_report_class()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    generated: list[Path] = []
    for path in files:
        try:
            report_path = generate_report(
                path=path,
                output_dir=output_dir,
                full=args.full,
                sample_size=args.sample_size,
                minimal=args.minimal,
                random_state=args.random_state,
                profile_report_cls=profile_report_cls,
            )
            generated.append(report_path)
            print(f"Report written to {report_path}")
        except Exception as error:
            print(f"Error generating report for {path.name}: {error}", file=sys.stderr)

    return 0 if generated else 1


# ==================== EXECUTION ====================

if __name__ == "__main__":
    raise SystemExit(main())
