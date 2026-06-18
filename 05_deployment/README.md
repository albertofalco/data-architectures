# Module 05: Deployment

## General Description

This module provides an educational deployment layer for the data architecture
pipeline. It simulates production batch inference, exposes lightweight run and
prediction browsing through FastAPI, persists model predictions in ClickHouse,
and provides an Apache Superset service for Data Warehouse exploration.

The module consumes artifacts produced by previous modules:

- **Normalized data**: `data/db_input/application_train/application_train.csv`,
  produced by `01_data_normalization`.
- **Operational database**: MySQL tables loaded by `02_database_connections`.
- **Data Warehouse outputs**: ClickHouse tables and DW parquet files produced
  by `03_dw_pipeline`.
- **ML artifacts**: model bundles, metrics, and predictions under
  `data/ml_outputs/`, produced by `04_ml_development`.

Scripts are run directly from the repository root. The module does not expose a
package entrypoint.

## Requirements

Install the module requirements from the repository root after activating the
project virtual environment:

```bash
source venv/bin/activate
python -m pip install -r 05_deployment/requirements.txt
```

Main dependencies:

- fastapi
- uvicorn
- Jinja2
- PyYAML
- pandas
- pyarrow
- SQLAlchemy
- mysql-connector-python
- clickhouse-connect
- psutil

The module reads `.env` from the repository root. MySQL and ClickHouse variables
must match the services used by modules `02` and `03`. Docker Compose also
requires Superset environment variables. Use placeholders in shared
documentation and keep real values only in the local, gitignored `.env` file:

```bash
SUPERSET_SECRET_KEY=<superset-secret-key>
SUPERSET_ADMIN_USERNAME=<superset-admin-username>
SUPERSET_ADMIN_PASSWORD=<superset-admin-password>
SUPERSET_ADMIN_FIRSTNAME=<superset-admin-first-name>
SUPERSET_ADMIN_LASTNAME=<superset-admin-last-name>
SUPERSET_ADMIN_EMAIL=<superset-admin-email>
```

## Main Functionalities

### Holdout Batch Simulation

`generate_holdout_assets.py` creates immutable holdout ID and private truth
assets by comparing the raw `application_train.csv` file against the Data
Warehouse parquet output. `insert_holdout_batch.py` then inserts the next
ordered holdout slice into MySQL and writes a manifest under
`data/ml_outputs/inference_runs/`.

`TARGET` is removed before inserting rows into MySQL. It is retained only in the
private holdout truth asset for post-inference evaluation.

### Manifest-Scoped Data Warehouse Refresh

`refresh_dw_batch.py` inserts only the manifest entity IDs from the ClickHouse
MySQL staging table into the ClickHouse storage table. The script also records
storage and reporting row counts in the manifest.

The full `03_dw_pipeline` scripts are not re-run from this module, which avoids
duplicating previously loaded rows.

### Batch Inference Orchestration

`run_inference_batch.py` reuses the scoring layer from
`04_ml_development/src/scoring`. It scores only the `SK_ID_CURR` values listed
in the manifest, writes local prediction parquet files and metrics JSON files,
and optionally persists predictions into ClickHouse.

The default deployment models are configured in
`05_deployment/config/deployment.yml`:

- `xgboost`
- `tabpfn_mix`
- `pyod_autoencoder`

`tabpfn_mix` and `pyod_autoencoder` use the Python 3.13 foundation-model Docker
runtime image: `data-architectures-foundation:py313`.

### Deployment API and Web UI

The FastAPI application exposes JSON endpoints and server-rendered HTML views
for deployment runs, model summaries, and prediction previews.

### Superset Runtime

`docker-compose.yml` defines a Superset image with `clickhouse-connect`
installed, a one-shot initialization service, and the main Superset web service.

## Configuration

Runtime defaults are stored in `05_deployment/config/deployment.yml`.

Important defaults:

- `defaults.entity_key`: `SK_ID_CURR`
- `defaults.target`: `TARGET`
- `defaults.source_name`: `clickhouse`
- `defaults.batch_size`: `1000`
- `defaults.models`: deployment model list
- `clickhouse.database`: ClickHouse DW database
- `clickhouse.staging_database`: ClickHouse MySQL-engine staging database
- `clickhouse.predictions_table`: prediction table name
- `api.port`: FastAPI web port
- `superset.port`: Superset web port

Create the ClickHouse prediction table before persisting inference outputs:

```bash
clickhouse-client --queries-file 05_deployment/sql/create_ml_predictions.sql
```

## Execution Instructions

### Prerequisites

1. Activate the project virtual environment.
2. Install `05_deployment/requirements.txt`.
3. Ensure previous pipeline modules have produced the required local data and
   database state.
4. Configure `.env` locally with MySQL, ClickHouse, and Superset variables.
5. Create the ClickHouse `ml_predictions` table.
6. Build the foundation-model Docker image before scoring Docker-backed models.

### Build the Foundation Runtime Image

Run the Docker build command from the repository root when using
`tabpfn_mix` or `pyod_autoencoder`:

```bash
docker build \
  -f 04_ml_development/docker/Dockerfile.foundation \
  -t data-architectures-foundation:py313 \
  .
```

### Run the Deployment Batch Flow

These commands can modify MySQL, ClickHouse, and local artifacts under
`data/ml_outputs/`. Run them only during an authorized deployment or validation
phase.

```bash
# 1. Generate immutable holdout ID and truth assets.
python 05_deployment/scripts/generate_holdout_assets.py

# 2. Insert the next ordered holdout batch into MySQL and write a manifest.
python 05_deployment/scripts/insert_holdout_batch.py --rows 1000

# 3. Refresh ClickHouse storage/reporting rows for the manifest.
python 05_deployment/scripts/refresh_dw_batch.py --manifest <run_id>

# 4. Run manifest-scoped inference and persist predictions.
python 05_deployment/scripts/run_inference_batch.py --manifest <run_id>

# 5. Measure local deployment artifact storage.
python 05_deployment/scripts/measure_storage.py --run-id <run_id>
```

### Dry-Run and Planning Commands

Use these commands to validate inputs and inspect planned work before writing to
databases:

```bash
python 05_deployment/scripts/insert_holdout_batch.py --rows 1000 --dry-run
python 05_deployment/scripts/insert_holdout_batch.py --rows 1000 --manifest-only
python 05_deployment/scripts/refresh_dw_batch.py --manifest <run_id> --dry-run
python 05_deployment/scripts/run_inference_batch.py --manifest <run_id> --models xgboost --dry-run
python 05_deployment/scripts/run_inference_batch.py --manifest <run_id> --skip-clickhouse
python 05_deployment/scripts/measure_storage.py --run-id <run_id> --include-databases
```

### Run the API Locally

```bash
uvicorn app.main:app \
  --app-dir 05_deployment/api \
  --host 0.0.0.0 \
  --port 8050
```

The web UI is available at:

```text
http://localhost:8050
```

### API Endpoints

- `GET /health`
- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/model-summaries`
- `GET /api/predictions?run_id=<run_id>&model_name=<model>&limit=100`
- `POST /api/inference/batch`
- `GET /`
- `GET /runs/{run_id}`

### Run Docker Compose Services

Validate and start the deployment services:

```bash
docker compose -f 05_deployment/docker-compose.yml config
docker compose -f 05_deployment/docker-compose.yml build
docker compose -f 05_deployment/docker-compose.yml up
```

Services:

- `ml-api-web`: FastAPI web application at `http://localhost:8050`
- `superset-init`: one-shot Superset metastore and admin bootstrap service
- `superset`: Superset web application at `http://localhost:8088`

Inside Docker containers, use `host.docker.internal` when connecting to
services exposed by the host.

## Output Artifacts

Default configured outputs:

- `data/assets/holdout_application_train_ids.csv`
- `data/assets/holdout_application_train_truth.csv`
- `data/ml_outputs/inference_runs/<run_id>.json`
- `data/ml_outputs/predictions/<model>_<run_id>_predictions.parquet`
- `data/ml_outputs/metrics/<model>_<run_id>_predictions_metrics.json`
- `data/ml_outputs/metrics/<run_id>_storage_metrics.json`

Prediction rows persisted to ClickHouse use the DDL in
`05_deployment/sql/create_ml_predictions.sql`.

## Testing

The tests use local fixtures and dry-run paths to avoid real database
connections unless a script explicitly requires them:

```bash
python -m pytest 05_deployment/tests/
```

A `fastapi.testclient.TestClient` smoke test is documented but skipped in the
Python 3.14 development environment because the client hangs there.

## Operational Notes

- Do not commit `.env`, generated `data/` contents, model bundles, metrics,
  predictions, or manifests.
- `insert_holdout_batch.py` reads from the normalized
  `application_train.csv` file because it contains normalized columns such as
  `ORGANIZATION_TYPE_ID` and `ORGANIZATION_TYPE_2_ID`.
- `run_inference_batch.py` adds holdout metrics when the private truth asset is
  available.
- If `refresh_dw_batch.py` reports fewer rows in `rep_application_train` than
  expected, inspect the materialized view state or run a manifest-scoped
  reporting backfill before scoring.
