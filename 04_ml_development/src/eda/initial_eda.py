"""Initial EDA workflow for local Data Warehouse parquet files."""

# ==================== IMPORTS ====================

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from common.config import configured_path, find_parquet_files, load_config


# ==================== CONFIGURATION ====================

TARGET_COL = "TARGET"
SUMMARY_FILENAME = "eda_summary.md"
MAX_COLUMN_SUMMARY_ROWS = 120
MAX_LOW_VARIANCE_ROWS = 10
MAX_TARGET_CORRELATION_ROWS = 10
MAX_HEATMAP_COLUMNS = 60


# ==================== HELPER FUNCTIONS ====================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the EDA workflow."""
    parser = argparse.ArgumentParser(
        description="Generate initial EDA summaries for DW parquet files."
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
        help="Directory for EDA outputs. Defaults to paths.eda_reports in config.yml.",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=None,
        help="Optional parquet table stems or filenames to analyze.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Optional sample size for faster exploratory analysis.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed used when --sample-size is set.",
    )
    parser.add_argument(
        "--target-col",
        default=TARGET_COL,
        help="Target column used for target correlation output when present.",
    )
    return parser.parse_args()


def column_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize data types, nulls, and unique values by column."""
    null_count = df.isna().sum()
    return pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "null_count": null_count,
            "null_pct": (null_count / len(df) * 100).round(4) if len(df) else 0,
            "unique_count": df.nunique(dropna=True),
        }
    ).sort_index()


def low_variance_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize variance and cardinality for numeric columns."""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return pd.DataFrame(columns=["variance", "unique_count", "is_constant"])

    variances = numeric_df.var(numeric_only=True).sort_values()
    unique_counts = numeric_df.nunique(dropna=True)
    result = pd.DataFrame(
        {
            "variance": variances,
            "unique_count": unique_counts.reindex(variances.index),
        }
    )
    result["is_constant"] = result["unique_count"] <= 1
    return result


def correlation_outputs(
    df: pd.DataFrame,
    table_name: str,
    assets_dir: Path,
    target_col: str,
) -> dict[str, object]:
    """Calculate numeric correlations and create a bounded heatmap."""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return {
            "numeric_columns": numeric_df.shape[1],
            "target_correlations": pd.DataFrame(columns=["column", "correlation"]),
            "heatmap_path": None,
            "heatmap_skipped": "fewer than two numeric columns",
        }

    corr = numeric_df.corr()

    target_correlations = pd.DataFrame(columns=["column", "correlation"])
    if target_col in corr.columns:
        target_correlations = (
            corr[target_col]
            .drop(labels=[target_col], errors="ignore")
            .sort_values(key=lambda series: series.abs(), ascending=False)
            .rename("correlation")
            .reset_index()
            .rename(columns={"index": "column"})
        )

    heatmap_path: Path | None = None
    heatmap_skipped: str | None = None
    if corr.shape[0] <= MAX_HEATMAP_COLUMNS:
        assets_dir.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(12, 9))
        sns.heatmap(corr, cmap="coolwarm", center=0, ax=ax)
        ax.set_title(f"Correlation matrix - {table_name}")
        fig.tight_layout()
        heatmap_path = assets_dir / f"{table_name}_correlation_heatmap.png"
        fig.savefig(heatmap_path, dpi=140)
        plt.close(fig)
    else:
        heatmap_skipped = (
            f"correlation matrix has {corr.shape[0]} numeric columns, "
            f"above the {MAX_HEATMAP_COLUMNS} column heatmap limit"
        )

    return {
        "numeric_columns": numeric_df.shape[1],
        "target_correlations": target_correlations,
        "heatmap_path": heatmap_path,
        "heatmap_skipped": heatmap_skipped,
    }


def read_table(path: Path, sample_size: int | None, random_state: int) -> tuple[pd.DataFrame, bool]:
    """Read a parquet table and optionally return a reproducible sample."""
    df = pd.read_parquet(path)
    if sample_size and sample_size > 0 and len(df) > sample_size:
        return df.sample(n=sample_size, random_state=random_state), True
    return df, False


def analyze_file(
    path: Path,
    assets_dir: Path,
    sample_size: int | None,
    random_state: int,
    target_col: str,
) -> dict[str, object]:
    """Analyze one parquet file and return its EDA results."""
    table_name = path.stem
    print(f"Analyzing {path.name}")

    df, sampled = read_table(path, sample_size=sample_size, random_state=random_state)
    correlations = correlation_outputs(df, table_name, assets_dir, target_col)

    return {
        "table": table_name,
        "source_file": str(path),
        "rows_analyzed": len(df),
        "columns": len(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 4),
        "sampled": sampled,
        "column_summary": column_summary(df),
        "low_variance": low_variance_summary(df),
        "correlations": correlations,
    }


def dataframe_to_markdown(
    df: pd.DataFrame,
    index_name: str | None = None,
    max_rows: int | None = None,
) -> tuple[str, int]:
    """Convert a DataFrame to a Markdown table and return omitted row count."""
    table = df
    omitted = 0
    if max_rows is not None and len(table) > max_rows:
        omitted = len(table) - max_rows
        table = table.head(max_rows)

    if index_name is not None:
        table = table.reset_index().rename(columns={"index": index_name})

    return table.to_markdown(index=False), omitted


def relative_markdown_path(path: Path, start: Path) -> str:
    """Return a POSIX-style relative path for a Markdown link."""
    return Path(os.path.relpath(path, start=start)).as_posix()


def append_dataframe_section(
    lines: list[str],
    title: str,
    df: pd.DataFrame,
    empty_message: str,
    index_name: str | None = None,
    max_rows: int | None = None,
) -> None:
    """Append a bounded DataFrame as a section in a Markdown report."""
    lines.extend([f"#### {title}", ""])
    if df.empty:
        lines.extend([empty_message, ""])
        return

    markdown_table, omitted = dataframe_to_markdown(
        df=df,
        index_name=index_name,
        max_rows=max_rows,
    )
    lines.extend([markdown_table, ""])
    if omitted:
        lines.extend([f"_Mostrando {max_rows} de {len(df)} filas; {omitted} filas omitidas._", ""])


def write_run_summary(
    output_dir: Path,
    results: list[dict[str, object]],
    missing: list[str],
    target_col: str,
) -> Path:
    """Write the combined EDA results to a Markdown summary."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / SUMMARY_FILENAME
    assets_dir = summary_path.with_suffix("")
    lines = [
        "# Initial EDA Summary",
        "",
        f"- Report assets: `{assets_dir.name}/`",
        "",
    ]

    if missing:
        lines.extend(["## Missing Tables", ""])
        lines.extend(f"- `{table}`" for table in missing)
        lines.append("")

    lines.extend(["## Analyzed Tables", ""])
    for result in results:
        lines.extend(
            [
                f"### {result['table']}",
                "",
                f"- Source: `{result['source_file']}`",
                f"- Rows analyzed: {result['rows_analyzed']}",
                f"- Columns: {result['columns']}",
                f"- Memory: {result['memory_mb']} MB",
                f"- Sampled: {result['sampled']}",
                "",
            ]
        )

        append_dataframe_section(
            lines=lines,
            title="Column Summary",
            df=result["column_summary"],
            empty_message="No columns found.",
            index_name="column",
            max_rows=MAX_COLUMN_SUMMARY_ROWS,
        )
        append_dataframe_section(
            lines=lines,
            title="Low Variance Numeric Columns",
            df=result["low_variance"],
            empty_message="No numeric columns available for variance analysis.",
            index_name="column",
            max_rows=MAX_LOW_VARIANCE_ROWS,
        )

        correlations = result["correlations"]
        append_dataframe_section(
            lines=lines,
            title=f"Top Target Correlations",
            df=correlations["target_correlations"],
            empty_message=f"No target correlation output because `{target_col}` is absent or unavailable.",
            max_rows=MAX_TARGET_CORRELATION_ROWS,
        )

        heatmap_path = correlations["heatmap_path"]
        lines.extend(["#### Correlation Heatmap", ""])
        if heatmap_path is not None:
            relative_path = relative_markdown_path(Path(heatmap_path), start=summary_path.parent)
            lines.extend([f"![Correlation heatmap - {result['table']}]({relative_path})", ""])
        else:
            lines.extend([f"No heatmap generated: {correlations['heatmap_skipped']}.", ""])

        lines.append("")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path


# ==================== MAIN FUNCTIONS ====================

def main() -> int:
    """Run EDA for the selected parquet tables and return an exit code."""
    args = parse_args()
    config = load_config()
    data_dir = args.data_dir or configured_path(config, "dw_data", "./data/dw_parquet/")
    output_dir = args.output_dir or configured_path(
        config, "eda_reports", "./data/ml_outputs/eda_reports/"
    )
    summary_path = output_dir / SUMMARY_FILENAME
    assets_dir = summary_path.with_suffix("")

    try:
        files, missing = find_parquet_files(data_dir, args.tables)
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 1

    if not files:
        print(f"No parquet files found in {data_dir}", file=sys.stderr)
        return 1

    results: list[dict[str, object]] = []
    for path in files:
        try:
            results.append(
                analyze_file(
                    path=path,
                    assets_dir=assets_dir,
                    sample_size=args.sample_size,
                    random_state=args.random_state,
                    target_col=args.target_col,
                )
            )
        except Exception as error:
            print(f"Error analyzing {path.name}: {error}", file=sys.stderr)

    summary_path = write_run_summary(output_dir, results, missing, args.target_col)
    print(f"EDA summary written to {summary_path}")

    if missing:
        print(f"Missing tables: {', '.join(missing)}", file=sys.stderr)

    return 0 if results else 1


# ==================== EXECUTION ====================

if __name__ == "__main__":
    raise SystemExit(main())
