"""Model-ready feature table construction from DW report tables."""

# ==================== IMPORTS ====================

from __future__ import annotations

from typing import Any

import polars as pl

from data_access.contracts import FeatureSource
from data_engineering.aggregations import aggregate_bureau_balance, aggregate_by_key
from data_engineering.joins import left_join_features


# ==================== MAIN CLASSES ====================

class FeatureBuilder:
    """Create one-row-per-customer features from multiple DW tables."""

    def __init__(self, source: FeatureSource, config: dict[str, Any]):
        """Initialize the source and configured entity, target, and base table names."""
        self.source = source
        self.config = config
        self.pipeline_config = config.get("ml_pipeline", {})
        self.entity_key = self.pipeline_config.get("entity_key", "SK_ID_CURR")
        self.target = self.pipeline_config.get("target", "TARGET")
        self.base_table = self.pipeline_config.get("base_table", "rep_application_train")

    def build(
        self,
        limit: int | None = None,
        entity_ids: list[int | str] | None = None,
    ) -> pl.LazyFrame:
        """Build one row per entity by aggregating the configured feature tables."""
        base = self.source.load_table(
            self.base_table,
            limit=limit,
            entity_ids=entity_ids,
            entity_key=self.entity_key,
        ).unique(subset=[self.entity_key])
        scoped_entity_ids: list[int | str] | None = entity_ids
        if scoped_entity_ids is None and limit is not None:
            scoped_entity_ids = (
                base.select(self.entity_key).collect().get_column(self.entity_key).to_list()
            )
        feature_frames: list[pl.LazyFrame] = []

        for table_config in self.pipeline_config.get("feature_tables", {}).values():
            table_name = table_config["table"]
            prefix = table_config["prefix"]
            if "bridge_table" in table_config:
                bridge = self.source.load_table(
                    table_config["bridge_table"],
                    entity_ids=scoped_entity_ids,
                    entity_key=self.entity_key,
                )
                bridge_ids = (
                    bridge.select(table_config["bridge_key"])
                    .collect()
                    .get_column(table_config["bridge_key"])
                    .to_list()
                    if scoped_entity_ids is not None
                    else None
                )
                feature_frames.append(
                    aggregate_bureau_balance(
                        balance=self.source.load_table(
                            table_name,
                            entity_ids=bridge_ids,
                            entity_key=table_config["bridge_key"],
                        ),
                        bureau=bridge,
                        bridge_key=table_config["bridge_key"],
                        entity_key=table_config["entity_key"],
                        prefix=prefix,
                    )
                )
                continue

            feature_frames.append(
                aggregate_by_key(
                    frame=self.source.load_table(
                        table_name,
                        entity_ids=scoped_entity_ids,
                        entity_key=table_config["key"],
                    ),
                    key=table_config["key"],
                    prefix=prefix,
                )
            )

        return left_join_features(base=base, feature_frames=feature_frames, key=self.entity_key)

    def collect(
        self,
        limit: int | None = None,
        entity_ids: list[int | str] | None = None,
    ) -> pl.DataFrame:
        """Build and materialize the feature table as a Polars DataFrame."""
        return self.build(limit=limit, entity_ids=entity_ids).collect()
