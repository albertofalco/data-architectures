"""Tests for ClickHouse refresh planning."""

# ==================== IMPORTS ====================

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from conftest import load_script_module


# ==================== TESTS ====================

def test_refresh_dry_run_prints_sql_without_connecting(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dry-run emits insert and validation SQL but does not connect."""
    runs_dir = Path(deployment_config["paths"]["inference_runs"])
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "run_1.json").write_text(
        json.dumps({"run_id": "run_1", "entity_ids": [101, 102]}),
        encoding="utf-8",
    )
    module = load_script_module("refresh_dw_batch")
    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(module, "clickhouse_client_from_env", lambda: pytest.fail("ClickHouse should not be used"))
    monkeypatch.setattr(sys, "argv", ["refresh_dw_batch.py", "--manifest", "run_1", "--dry-run"])

    assert module.main() == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["entity_count"] == 2
    assert "INSERT INTO data_arch_dw.application_train" in payload["insert_sql"]
    assert "staging_mysql.application_train" in payload["insert_sql"]
    assert "rep_application_train" in payload["post_refresh_reporting_count_sql"]
    assert "no ClickHouse connection" in payload["note"]


def test_refresh_rejects_duplicate_manifest_ids(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Manifest entity IDs must be unique before SQL is generated."""
    runs_dir = Path(deployment_config["paths"]["inference_runs"])
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "run_1.json").write_text(
        json.dumps({"run_id": "run_1", "entity_ids": [101, 101]}),
        encoding="utf-8",
    )
    module = load_script_module("refresh_dw_batch")
    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(sys, "argv", ["refresh_dw_batch.py", "--manifest", "run_1", "--dry-run"])

    with pytest.raises(ValueError, match="duplicate"):
        module.main()
