"""CLI wrapper for evaluating a saved bundle on an engineered feature table."""

# ==================== IMPORTS ====================

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _bootstrap import add_src_to_path

add_src_to_path()

from common.config import configured_path, load_config
from common.paths import feature_output_path
from preprocessing.column_selection import split_features_target
from training.evaluate_model import evaluate_adapter
from training.model_registry import load_bundle


# ==================== HELPER FUNCTIONS ====================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for model evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate a saved model bundle.")
    parser.add_argument("--model-uri", "--run-id", dest="model_uri", type=Path, required=True)
    parser.add_argument("--features-path", type=Path, default=None)
    return parser.parse_args()


# ==================== MAIN FUNCTIONS ====================

def main() -> int:
    """Evaluate a model bundle, persist metrics, and return a success code."""
    args = parse_args()
    config = load_config()
    bundle = load_bundle(args.model_uri)
    df = pd.read_parquet(args.features_path or feature_output_path(config))
    X, y = split_features_target(df, config=config, require_target=True)
    X = X.reindex(columns=bundle["feature_columns"], fill_value=0)
    X_prepared = bundle["preprocessor"].transform(X)
    metrics = evaluate_adapter(bundle["adapter"], X_prepared, y, metric_prefix="full_")
    metrics_dir = configured_path(config, "metrics", "./data/ml_outputs/metrics/")
    output_path = metrics_dir / f"{bundle['model_name']}_evaluation_metrics.json"
    output_path.write_text(pd.Series(metrics).to_json(indent=2), encoding="utf-8")
    print(f"Evaluation metrics written to {output_path}")
    return 0


# ==================== EXECUTION ====================

if __name__ == "__main__":
    raise SystemExit(main())
