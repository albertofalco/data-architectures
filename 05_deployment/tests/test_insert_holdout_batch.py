"""Tests for controlled holdout insertion planning."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

from conftest import load_script_module


def _write_holdout_inputs_with_size(config: dict, size: int) -> None:
    """Create holdout assets and normalized source files with deterministic IDs."""
    holdout_ids_path = Path(config["paths"]["holdout_ids"])
    truth_path = Path(config["paths"]["holdout_truth"])
    normalized_path = Path(config["paths"]["normalized_application_train"])
    holdout_ids_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    ranks = list(range(1, size + 1))
    ids = [100000 + rank for rank in ranks]
    pd.DataFrame({"holdout_rank": ranks, "SK_ID_CURR": ids}).to_csv(holdout_ids_path, index=False)
    pd.DataFrame({"SK_ID_CURR": ids, "TARGET": [rank % 2 for rank in ranks]}).to_csv(truth_path, index=False)
    pd.DataFrame(
        {
            "SK_ID_CURR": ids,
            "TARGET": [rank % 2 for rank in ranks],
            "feature": ranks,
        }
    ).to_csv(normalized_path, index=False)


def _write_holdout_inputs(config: dict) -> None:
    """Create minimal holdout assets and normalized source files."""
    _write_holdout_inputs_with_size(config, 3)


def _write_manifest(config: dict, payload: dict) -> None:
    """Write a local inference manifest fixture."""
    runs_dir = Path(config["paths"]["inference_runs"])
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = payload["run_id"]
    (runs_dir / f"{run_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_dry_run_selects_ordered_holdout_without_writing_manifest(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dry-run prepares the next ordered slice and does not write a manifest."""
    _write_holdout_inputs(deployment_config)
    module = load_script_module("insert_holdout_batch")
    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(
        sys,
        "argv",
        ["insert_holdout_batch.py", "--rows", "2", "--run-id", "run_1", "--dry-run"],
    )

    assert module.main() == 0

    manifest = ast.literal_eval(capsys.readouterr().out.strip())
    assert manifest["status"] == "planned"
    assert manifest["previous_consumed_rank_max"] == 0
    assert manifest["entity_ids"] == [100001, 100002]
    assert manifest["rows_inserted"] == 0
    assert manifest["target_removed"] is True
    assert not (Path(deployment_config["paths"]["inference_runs"]) / "run_1.json").exists()


def test_manifest_only_writes_manifest_without_mysql(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Manifest-only records the batch plan and never opens a MySQL connection."""
    _write_holdout_inputs(deployment_config)
    module = load_script_module("insert_holdout_batch")
    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(module, "mysql_engine_from_env", lambda: pytest.fail("MySQL should not be used"))
    monkeypatch.setattr(
        sys,
        "argv",
        ["insert_holdout_batch.py", "--rows", "2", "--run-id", "run_1", "--manifest-only"],
    )

    assert module.main() == 0

    manifest_path = Path(deployment_config["paths"]["inference_runs"]) / "run_1.json"
    assert manifest_path.exists()
    assert '"status": "manifest_only"' in manifest_path.read_text(encoding="utf-8")


def test_dry_run_starts_after_inserted_manifest_rank_10(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Inserted ranks 1-10 are skipped before selecting the next 1000 rows."""
    _write_holdout_inputs_with_size(deployment_config, 1100)
    _write_manifest(
        deployment_config,
        {
            "run_id": "run_0",
            "status": "inserted",
            "holdout_start_rank": 1,
            "holdout_end_rank": 10,
            "rows_inserted": 10,
            "entity_ids": list(range(100001, 100011)),
        },
    )
    module = load_script_module("insert_holdout_batch")
    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(
        sys,
        "argv",
        ["insert_holdout_batch.py", "--rows", "1000", "--run-id", "run_1", "--dry-run"],
    )

    assert module.main() == 0

    manifest = ast.literal_eval(capsys.readouterr().out.strip())
    assert manifest["previous_consumed_rank_max"] == 10
    assert manifest["holdout_start_rank"] == 11
    assert manifest["holdout_end_rank"] == 1010
    assert manifest["rows_selected"] == 1000
    assert manifest["entity_ids"][0] == 100011
    assert manifest["entity_ids"][-1] == 101010


def test_dry_run_starts_after_inserted_manifest_rank_1010(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A later inserted 1000-row batch advances the next cursor to rank 1011."""
    _write_holdout_inputs_with_size(deployment_config, 1200)
    _write_manifest(
        deployment_config,
        {
            "run_id": "run_1",
            "status": "inserted",
            "holdout_start_rank": 11,
            "holdout_end_rank": 1010,
            "rows_inserted": 1000,
            "entity_ids": list(range(100011, 101011)),
        },
    )
    module = load_script_module("insert_holdout_batch")
    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(
        sys,
        "argv",
        ["insert_holdout_batch.py", "--rows", "10", "--run-id", "run_2", "--dry-run"],
    )

    assert module.main() == 0

    manifest = ast.literal_eval(capsys.readouterr().out.strip())
    assert manifest["previous_consumed_rank_max"] == 1010
    assert manifest["holdout_start_rank"] == 1011
    assert manifest["holdout_end_rank"] == 1020
    assert manifest["rows_selected"] == 10


def test_manifest_only_does_not_advance_consumed_rank(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Uninserted manifest-only runs do not skip holdout rows."""
    _write_holdout_inputs_with_size(deployment_config, 20)
    _write_manifest(
        deployment_config,
        {
            "run_id": "run_manifest_only",
            "status": "manifest_only",
            "holdout_start_rank": 1,
            "holdout_end_rank": 10,
            "rows_inserted": 0,
            "entity_ids": list(range(100001, 100011)),
        },
    )
    module = load_script_module("insert_holdout_batch")
    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(
        sys,
        "argv",
        ["insert_holdout_batch.py", "--rows", "2", "--run-id", "run_1", "--dry-run"],
    )

    assert module.main() == 0

    manifest = ast.literal_eval(capsys.readouterr().out.strip())
    assert manifest["previous_consumed_rank_max"] == 0
    assert manifest["holdout_start_rank"] == 1
    assert manifest["entity_ids"] == [100001, 100002]


def test_selected_batch_overlapping_inserted_ids_is_rejected(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A selected batch must not reuse IDs from inserted manifests."""
    _write_holdout_inputs_with_size(deployment_config, 20)
    _write_manifest(
        deployment_config,
        {
            "run_id": "run_inconsistent",
            "status": "inserted",
            "holdout_start_rank": 20,
            "holdout_end_rank": 20,
            "rows_inserted": 1,
            "entity_ids": [100001],
        },
    )
    module = load_script_module("insert_holdout_batch")
    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(module, "consumed_rank_max", lambda config: 0)
    monkeypatch.setattr(sys, "argv", ["insert_holdout_batch.py", "--rows", "2", "--dry-run"])

    with pytest.raises(RuntimeError, match="overlaps already inserted IDs"):
        module.main()


def test_duplicate_holdout_ids_are_rejected(
    deployment_config: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Holdout assets must be immutable one-to-one ID lists."""
    _write_holdout_inputs(deployment_config)
    pd.DataFrame(
        {
            "holdout_rank": [1, 2],
            "SK_ID_CURR": [101, 101],
        }
    ).to_csv(deployment_config["paths"]["holdout_ids"], index=False)
    module = load_script_module("insert_holdout_batch")
    monkeypatch.setattr(module, "load_deployment_config", lambda: deployment_config)
    monkeypatch.setattr(sys, "argv", ["insert_holdout_batch.py", "--rows", "2", "--dry-run"])

    with pytest.raises(ValueError, match="duplicate"):
        module.main()
