"""CLI wrapper for hyperparameter tuning."""

# ==================== IMPORTS ====================

from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()

from common.config import load_config
from tuning.tune_model import tune_model


# ==================== HELPER FUNCTIONS ====================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for hyperparameter tuning."""
    parser = argparse.ArgumentParser(description="Tune a supported model family.")
    parser.add_argument(
        "--model",
        choices=[
            "random_forest",
            "xgboost",
            "local_neural_net",
            "tabicl",
            "tabpfn_mix",
            "pyod_autoencoder",
        ],
        required=True,
    )
    parser.add_argument("--features-path", type=Path, default=None)
    return parser.parse_args()


# ==================== MAIN FUNCTIONS ====================

def main() -> int:
    """Tune one model family, persist results, and return a success code."""
    args = parse_args()
    output_path = tune_model(load_config(), args.model, args.features_path)
    print(f"Tuning results written to {output_path}")
    return 0


# ==================== EXECUTION ====================

if __name__ == "__main__":
    raise SystemExit(main())
