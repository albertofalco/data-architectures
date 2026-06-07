"""Feature joining helpers."""

from __future__ import annotations

from functools import reduce

import polars as pl


def left_join_features(base: pl.LazyFrame, feature_frames: list[pl.LazyFrame], key: str) -> pl.LazyFrame:
    """Left join a list of feature frames onto the base entity frame."""
    if not feature_frames:
        return base
    return reduce(lambda left, right: left.join(right, on=key, how="left"), feature_frames, base)
