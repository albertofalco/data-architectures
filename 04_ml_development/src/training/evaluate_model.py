"""Model evaluation utilities."""

# ==================== IMPORTS ====================

from __future__ import annotations

import numpy as np


# ==================== HELPER FUNCTIONS ====================

def positive_class_scores(probabilities) -> np.ndarray:
    """Return positive-class scores from predict_proba output."""
    scores = np.asarray(probabilities)
    if scores.ndim == 2 and scores.shape[1] > 1:
        return scores[:, 1]
    return scores.reshape(-1)


def classification_metrics(y_true, y_pred, y_score) -> dict[str, float]:
    """Compute precision, recall, F1, ROC-AUC, and PR-AUC metrics."""
    from sklearn.metrics import (
        average_precision_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    metrics = {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    try:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
    except ValueError:
        metrics["roc_auc"] = 0.0
    try:
        metrics["pr_auc"] = float(average_precision_score(y_true, y_score))
    except ValueError:
        metrics["pr_auc"] = 0.0
    return metrics


def evaluate_adapter(adapter, X, y, metric_prefix: str = "") -> dict[str, float]:
    """Evaluate an adapter and return prefixed metrics."""
    predictions = adapter.predict(X)
    scores = positive_class_scores(adapter.predict_proba(X))
    metrics = classification_metrics(y, predictions, scores)
    return {f"{metric_prefix}{name}": value for name, value in metrics.items()}
