"""Production scoring benchmark use case."""

# ==================== IMPORTS ====================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from common.config import configured_path
from scoring.batch_score import batch_score


# ==================== MAIN FUNCTIONS ====================

def benchmark_production(
    config: dict[str, Any],
    model_uri: Path,
    batch_sizes: list[int],
    source_name: str = "clickhouse",
) -> Path:
    """Run several batch sizes and persist their combined scoring metrics."""
    rows = []
    metrics_dir = configured_path(config, "metrics", "./data/ml_outputs/metrics/")
    model_name = Path(model_uri).stem.replace("_bundle", "")

    for size in batch_sizes:
        prediction_path = batch_score(
            config=config,
            model_uri=model_uri,
            source_name=source_name,
            limit=size,
        )
        metrics_path = metrics_dir / f"{model_name}_batch_score_metrics.json"
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics["prediction_path"] = str(prediction_path)
        rows.append(metrics)

    output_path = metrics_dir / f"{model_name}_production_benchmark.json"
    output_path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
