# Module 05: Deployment

## Objective

This module provides a deployment layer for the data architecture pipeline. It simulates production batch inference, exposes lightweight run and prediction browsing through FastAPI, persists model predictions in ClickHouse, and provides an Apache Superset service for data warehouse exploration.

The module consumes artifacts produced by previous modules:

- **Normalized data**: `data/db_input/application_train/application_train.csv`, produced by `01_data_normalization`.
- **Operational database**: MySQL tables loaded by `02_database_connections`.
- **Data Warehouse outputs**: ClickHouse tables and DW parquet files produced by `03_dw_pipeline`.
- **ML artifacts**: model bundles, metrics, and predictions under `data/ml_outputs/`, produced by `04_ml_development`.

Scripts are run directly from the repository root. The module does not expose a package entrypoint.

## Requirements

- fastapi
- uvicorn[standard]
- Jinja2
- python-multipart
- PyYAML
- pandas
- pyarrow
- SQLAlchemy
- mysql-connector-python
- clickhouse-connect
- psutil

## Main Functionalities

### Holdout Batch Simulation

`generate_holdout_assets.py` creates immutable holdout ID and private truth assets by comparing the raw `application_train.csv` file against the Data Warehouse parquet output. `insert_holdout_batch.py` then inserts the next ordered holdout slice into MySQL and writes a manifest under `data/ml_outputs/inference_runs`.

`TARGET` is removed before inserting rows into MySQL. It is retained only in the private holdout truth asset for post-inference evaluation.

### Manifest-Scoped Data Warehouse Refresh

`refresh_dw_batch.py` inserts only the manifest entity IDs from the ClickHouse MySQL staging table into the ClickHouse storage table. The script also records storage and reporting row counts in the manifest.

The full `03_dw_pipeline` scripts are not re-run from this module, which avoids duplicating previously loaded rows.

### Batch Inference Orchestration

`run_inference_batch.py` reuses the scoring layer from `04_ml_development/src/scoring`. It scores only the `SK_ID_CURR` values listed in the manifest, writes local prediction parquet files and metrics JSON files, and optionally persists predictions into ClickHouse.

The default deployment models are configured in `05_deployment/config/deployment.yml`:

- `xgboost`
- `tabpfn_mix`
- `pyod_autoencoder`

`tabpfn_mix` and `pyod_autoencoder` use the Python 3.13 foundation-model Docker runtime image: `data-architectures-foundation:py313`.

### Deployment API and Web UI

The FastAPI application exposes JSON endpoints and server-rendered HTML views for deployment runs, model summaries, and prediction previews.

### Superset Runtime

`docker-compose.yml` defines a Superset image with `clickhouse-connect` installed, a one-shot initialization service, and the main Superset web service.

### Runtime Configuration

`05_deployment/config/deployment.yml` defines the entity key, target, data source, batch size, deployment models, ClickHouse databases and prediction table, and the API and Superset ports.

## Execution Instructions

### Prerequisites

1. Activate the project virtual environment and install the module requirements from the repository root:

   ```bash
   source venv/bin/activate
   python -m pip install -r 05_deployment/requirements.txt
   ```

2. Ensure previous pipeline modules have produced the required local data and database state.
3. Configure the local, gitignored `.env` file. MySQL and ClickHouse variables must match the services used by modules `02` and `03`. Docker Compose also requires these Superset variables:

   ```bash
   SUPERSET_SECRET_KEY=<superset-secret-key>
   SUPERSET_ADMIN_USERNAME=<superset-admin-username>
   SUPERSET_ADMIN_PASSWORD=<superset-admin-password>
   SUPERSET_ADMIN_FIRSTNAME=<superset-admin-first-name>
   SUPERSET_ADMIN_LASTNAME=<superset-admin-last-name>
   SUPERSET_ADMIN_EMAIL=<superset-admin-email>
   ```

4. Review the runtime defaults in `05_deployment/config/deployment.yml` and create the ClickHouse prediction table before persisting inference outputs:

   ```bash
   clickhouse-client --queries-file 05_deployment/sql/create_ml_predictions.sql
   ```

5. Build the foundation-model Docker image before scoring Docker-backed models, like `tabpfn_mix` or `pyod_autoencoder`:

    ```bash
    docker build \
      -f 04_ml_development/docker/Dockerfile.foundation \
      -t data-architectures-foundation:py313 \
      .
    ```

### Run the Deployment Batch Flow

These commands can modify MySQL, ClickHouse, and local artifacts under `data/ml_outputs/`.

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

Commands to validate inputs and inspect planned work before writing to databases:

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
docker compose --env-file .env -f 05_deployment/docker-compose.yml config
docker compose --env-file .env -f 05_deployment/docker-compose.yml build
docker compose --env-file .env -f 05_deployment/docker-compose.yml up
```

Services:

- `ml-api-web`: FastAPI web application at `http://localhost:8050`
- `superset-init`: one-shot Superset metastore and admin bootstrap service; `Exited (0)` is the expected state after it completes
- `superset`: Superset web application at `http://localhost:8088`

`ml-api-web` and `superset` use `restart: unless-stopped` so Docker can bring them back after a host or Docker daemon restart.

Inside Docker containers, use `host.docker.internal` when connecting to services exposed by the host.

## Tests

The tests use local fixtures and dry-run paths to avoid real database connections unless a script explicitly requires them:

- `tests/test_insert_holdout_batch.py`: validates ordered holdout selection, manifest-only behavior, and duplicate or overlapping ID rejection.
- `tests/test_refresh_dw_batch.py`: validates dry-run SQL generation and duplicate manifest ID rejection.
- `tests/test_run_inference_batch.py`: validates input handling, model failure isolation, and Docker-backed foundation-model scoring.
- `tests/test_api.py`: validates run and prediction services, prediction previews, model summaries, path remapping, and inference command construction.

```bash
python -m pytest 05_deployment/tests/
```