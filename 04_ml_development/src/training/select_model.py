"""Model selection helpers."""

# ==================== IMPORTS ====================

from __future__ import annotations

from pathlib import Path

import pandas as pd


# ==================== HELPER FUNCTIONS ====================

def select_best_model(metrics_files: list[Path], metric: str = "test_pr_auc") -> pd.DataFrame:
    """Rank models from JSON metric files."""
    rows = []
    for path in metrics_files:
        rows.append(pd.read_json(path, typ="series").to_dict())
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(metric, ascending=False)
