"""Encoder factories."""

# ==================== IMPORTS ====================

from __future__ import annotations


# ==================== HELPER FUNCTIONS ====================

def categorical_encoder(min_frequency: int | None = None):
    """Return a one-hot encoder compatible with older and newer sklearn versions."""
    from sklearn.preprocessing import OneHotEncoder

    try:
        return OneHotEncoder(handle_unknown="ignore", min_frequency=min_frequency, sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)
