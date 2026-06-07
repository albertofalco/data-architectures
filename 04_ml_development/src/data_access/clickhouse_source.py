"""ClickHouse implementation of feature table access."""

from __future__ import annotations

import os
from typing import Iterable

import polars as pl
from dotenv import load_dotenv


class ClickHouseFeatureSource:
    """Load DW report tables from ClickHouse for production batch scoring."""

    def __init__(self, database: str | None = None):
        """Initialize the ClickHouseFeatureSource."""
        load_dotenv()
        self.database = database or os.getenv("CLICKHOUSE_DATABASE", "data_arch_dw")
        self.host = os.getenv("CLICKHOUSE_HOST", "localhost")
        self.port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
        self.user = os.getenv("CLICKHOUSE_USER", "default")
        self.password = os.getenv("CLICKHOUSE_PASSWORD", "")

    def _client(self):
        """Create a ClickHouse client."""
        try:
            import clickhouse_connect
        except ImportError as error:
            raise RuntimeError(
                "Missing dependency `clickhouse-connect`; install 03/04 requirements."
            ) from error
        return clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
        )

    @staticmethod
    def _format_in_values(values: Iterable[int | str]) -> str:
        """Format values for SQL IN clause, handling both strings and integers."""
        formatted = []
        for value in values:
            if isinstance(value, str):
                formatted.append("'" + value.replace("'", "''") + "'")
            else:
                formatted.append(str(int(value)))
        return ", ".join(formatted)

    def load_table(
        self,
        table_name: str,
        limit: int | None = None,
        entity_ids: list[int | str] | None = None,
        entity_key: str | None = None,
    ) -> pl.LazyFrame:
        """Load a table with an optional LIMIT for bounded production scoring."""
        query = f"SELECT * FROM {self.database}.{table_name}"
        if entity_ids is not None and entity_key is not None:
            if not entity_ids:
                query += " WHERE 0"
            else:
                values = self._format_in_values(entity_ids)
                query += f" WHERE {entity_key} IN ({values})"
        if limit is not None:
            query += f" LIMIT {int(limit)}"
        result = self._client().query_df(query)
        return pl.from_pandas(result).lazy()
