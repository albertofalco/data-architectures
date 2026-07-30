"""CLI wrapper for model training."""

# ==================== IMPORTS ====================

from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()

from common.config import load_config
from training.train_model import train_model


# ==================== HELPER FUNCTIONS ====================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for model training."""
    parser = argparse.ArgumentParser(description="Train one model family.")
    parser.add_argument(
        "--model",
        choices=[
            "random_forest",
            "xgboost",
            "local_neural_net",
            "mitra",
            "tabpfn_3",
            "tabpfn_mix",
            "tabicl",
            "pyod_autoencoder",
        ],
        required=True,
    )
    parser.add_argument("--features-path", type=Path, default=None)
    return parser.parse_args()


# ==================== MAIN FUNCTIONS ====================

def main() -> int:
    """Train and persist one model family, then return a success code."""
    args = parse_args()
    artifact_path = train_model(
        config=load_config(),
        model_name=args.model,
        features_path=args.features_path,
    )
    print(f"Model bundle written to {artifact_path}")
    return 0


# ==================== EXECUTION ====================

if __name__ == "__main__":
    raise SystemExit(main())
