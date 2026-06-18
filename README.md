# data-architectures

Data Architectures for Risk Management and Audit

## Modules

### 01_data_normalization

**Description:** Normalizes datasets applying relational database design principles (1NF, 2NF, 3NF), including atomization of values, creation of dimension tables, and resolution of shared dimension overlaps.

**Main script:** [`src/__main__.py`](01_data_normalization/src/__main__.py)

**Main features:**
- Standard Normalization: Data atomization (1NF) (e.g. atomization of ORGANIZATION_TYPE with creation of ORGANIZATION_TYPE_2 attribute)
- Design Optimization: Table decomposition into dimensions, and creation of reference/lookup tables
- Overlap Correction: Identifies and resolves inconsistencies in shared dimension tables (e.g. dim_name_contract_type, dim_weekday_appr_process_start)
- Output: Export of normalized datasets and dimension tables as CSV files

**Tests:**
- `test_content.py`: Validates content integrity by comparing normalized datasets with originals, verifying structure (shape), columns, and values for datasets like `application_train`, `bureau`, and `previous_application`

---

### 02_database_connections

**Description:** Python tool to automate data loading from CSV files to a MySQL database, with automatic schema creation, data integrity validation, and synchronization control.

**Main script:** [`src/__main__.py`](02_database_connections/src/__main__.py)

**Main features:**
- CSV to MySQL loading using SQLAlchemy and Pandas
- Connection to MySQL server via arguments or environment variables
- Automatic database creation if not exists
- Dynamic CSV file detection in data/db_input/
- Automatic data type inference
- Conversion of np.nan and None values to NULL
- TRUNCATE existing tables on reload

**Tests:**
- `test_db_connection.py`: Verifies database connectivity using both `mysql-connector-python` and `SQLAlchemy`
- `test_table_names.py`: Compares MySQL table names with CSV files in the folder to validate synchronization
- `test_integrity.py`: Table content control verifying integrity against source files, validating table names, structure (shape), columns, and values

---

### 03_dw_pipeline

**Description:** Creates and populates a dimensional data warehouse using ClickHouse as the analytical database. Connects to MySQL staging database via ClickHouse MySQL engine and creates an optimized storage layer with transactional tables, dictionaries, and materialized views.

**Main scripts:**
- [`dw_dbs_creator.py`](03_dw_pipeline/src/dw_dbs_creator.py): Creates staging and storage databases in ClickHouse
- [`dw_dict_creator.py`](03_dw_pipeline/src/dw_dict_creator.py): Creates dictionaries from dimension tables
- [`dw_tran_creator.py`](03_dw_pipeline/src/dw_tran_creator.py): Creates transactional (fact) tables
- [`dw_tran_insert.py`](03_dw_pipeline/src/dw_tran_insert.py): Inserts data into transactional tables
- [`dw_mv_creator.py`](03_dw_pipeline/src/dw_mv_creator.py): Creates report tables and materialized views
- [`dw_mv_insert.py`](03_dw_pipeline/src/dw_mv_insert.py): Inserts data into report tables

**Main features:**
- Database creation: Staging database uses MySQL engine for direct connection to source; storage database uses standard ClickHouse engine
- Dictionary creation: Creates ClickHouse dictionaries from dimension tables for fast lookups
- Transactional table creation: Two options - Option A (tables with defined PK from SK_ID columns) and Option B (tables without PK, adds _DW_ID column for sorting)
- Report table creation: Denormalized tables (rep_*) that replace IDs with descriptions using ClickHouse dictionaries, powered by materialized views (mv_*)

**Tests:**
- `test_connection_dw.py`: Verifies ClickHouse connectivity and lists available databases
- `test_raw_dw.py`: Verifies data integrity between CSV source files and report tables in ClickHouse, validating row count, columns, and content

---

### 04_ml_development

**Description:** Machine Learning development workspace for validating Data Warehouse parquet outputs, generating exploratory reports, building model-ready features, and running binary credit-risk model training, tuning, evaluation, and batch scoring.

**Main scripts:**
- [`test_initial_prep.py`](04_ml_development/tests/test_initial_prep.py): Validates raw CSV files against DW parquet report outputs
- [`build_features.py`](04_ml_development/scripts/build_features.py): Builds one-row-per-`SK_ID_CURR` feature tables from parquet or ClickHouse sources
- [`train.py`](04_ml_development/scripts/train.py): Trains one configured model family and persists a model bundle
- [`tune.py`](04_ml_development/scripts/tune.py): Runs Optuna hyperparameter tuning for supported model families
- [`evaluate.py`](04_ml_development/scripts/evaluate.py): Evaluates a saved model bundle against engineered features
- [`batch_score.py`](04_ml_development/scripts/batch_score.py): Runs production-style batch scoring from parquet or ClickHouse
- [`benchmark_production.py`](04_ml_development/scripts/benchmark_production.py): Benchmarks batch scoring throughput and latency

**Main features:**
- DW vs raw validation: Compares raw CSV source files with `rep_*` parquet outputs using table-specific rules from `04_ml_development/config.yml`
- EDA and profiling: Generates exploratory reports and HTML profile reports under `data/ml_outputs/`
- Feature engineering: Loads parquet or ClickHouse report tables, aggregates one-to-many tables by `SK_ID_CURR`, joins model features, and writes outputs to `data/ml_outputs/features/`
- Preprocessing: Applies target-safe column selection, imputation, encoding, and train/validation/test splitting
- Model adapters: Supports `random_forest`, `xgboost`, `local_neural_net`, `mitra`, `tabpfn_3`, `tabpfn_mix`, `tabicl`, and `pyod_autoencoder`
- Training and tuning: Persists model bundles, metrics, MLflow runs, Optuna tuning results, and performance logs under `data/ml_outputs/`
- Production scoring: Scores saved bundles from parquet or ClickHouse sources and records prediction outputs plus benchmark metrics

**Tests:**
- `test_initial_prep.py`: Validates DW parquet outputs against raw CSV inputs, checking structure, data types, null values, and content
- `test_ml_modular_pipeline.py`: Unit tests for parquet loading, feature building, target-safe preprocessing, performance logging, and model adapter behavior

---

### 05_deployment

**Description:** Deployment simulation layer for production-style batch inference, manifest-scoped Data Warehouse refresh, lightweight FastAPI monitoring, ClickHouse prediction persistence, and Apache Superset exploration.

**Main scripts and services:**
- [`generate_holdout_assets.py`](05_deployment/scripts/generate_holdout_assets.py): Generates immutable holdout ID and private truth assets from raw and DW data
- [`insert_holdout_batch.py`](05_deployment/scripts/insert_holdout_batch.py): Inserts the next ordered holdout batch into MySQL and writes a deployment manifest
- [`refresh_dw_batch.py`](05_deployment/scripts/refresh_dw_batch.py): Refreshes ClickHouse storage/reporting rows for the manifest entity IDs
- [`run_inference_batch.py`](05_deployment/scripts/run_inference_batch.py): Runs manifest-scoped batch inference using saved ML model bundles
- [`measure_storage.py`](05_deployment/scripts/measure_storage.py): Measures local deployment artifact storage and optional database footprint
- [`api/app/main.py`](05_deployment/api/app/main.py): FastAPI application for run, metric, and prediction browsing
- [`docker-compose.yml`](05_deployment/docker-compose.yml): Starts the deployment API and Superset services

**Main features:**
- Holdout simulation: Builds ordered production-like batches from `application_train` holdout rows while keeping `TARGET` in a private truth asset
- Controlled MySQL insertion: Inserts only selected manifest rows into the operational MySQL table and records batch metadata under `data/ml_outputs/inference_runs/`
- Incremental DW refresh: Moves manifest-scoped rows from ClickHouse MySQL staging into the ClickHouse storage/reporting layer without rerunning the full DW pipeline
- Batch inference orchestration: Reuses `04_ml_development` scoring logic to score saved model bundles for the manifest `SK_ID_CURR` values
- Prediction persistence: Writes local parquet predictions and metrics, and optionally persists prediction rows into `data_arch_dw.ml_predictions`
- Deployment UI: Provides JSON endpoints and HTML/Jinja views for runs, per-model summaries, and prediction previews
- Superset integration: Provides a Dockerized Superset runtime with ClickHouse connectivity for analytical dashboarding

**Tests:**
- `test_insert_holdout_batch.py`: Validates dry-run planning, manifest-only mode, ordered batch selection, duplicate rejection, and overlap protection
- `test_refresh_dw_batch.py`: Validates manifest-scoped ClickHouse SQL generation and duplicate entity ID rejection
- `test_run_inference_batch.py`: Validates inference planning, missing model handling, partial failure recording, and Docker-backed scoring delegation
- `test_api.py`: Unit tests for API handlers, run listing, prediction filtering, model summaries, and wide prediction previews
