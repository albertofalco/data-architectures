# Module 04: ML Development

## Objective

This module provides the machine learning development workspace for the data architecture pipeline. It validates data warehouse parquet outputs against the original raw CSV files, generates EDA profile reports, and includes a modular ML pipeline scaffold for binary credit-risk modeling.

The module consumes downstream outputs produced by the data warehouse pipeline:

- **Raw data**: CSV files stored under `data/raw/`
- **DW data**: parquet files stored under `data/dw_parquet/`
- **ML outputs**: reports and artifacts written under `data/ml_outputs/`

The module does not currently expose a package entrypoint. Scripts are run directly from the repository root.

## Requirements

Main dependencies:

- polars
- pyarrow
- pandas
- numpy
- matplotlib
- seaborn
- PyYAML
- tabulate
- python-dotenv
- scikit-learn
- imbalanced-learn
- xgboost
- optuna
- mlflow
- joblib
- torch
- huggingface-hub
- tabpfn
- tabicl
- autogluon.tabular with MITRA support, for Python versions lower than 3.14
- fg-data-profiling (requires Python `<3.14`, use Docker-based image `python:3.13-slim`)

## Main Functionalities

### DW vs Raw Validation

Compares Data Warehouse parquet outputs against raw CSV source files. The validation script checks structure, data types, null values, and content using table-specific rules from `04_ml_development/config.yml`.

### EDA Profile Report Generation

Generates HTML profile reports from DW parquet files using `fg-data-profiling`. The profiling script supports table selection, sampling, full-file profiling, and minimal/non-minimal report modes.

### ML Pipeline Scaffold

The module now includes a layered ML pipeline scaffold for binary credit-risk modeling over `rep_application_train.TARGET`. Training data is built from local DW parquet files; production-style scoring can read from the Data Warehouse through the ClickHouse adapter.

The ML code is intentionally modular:

- `src/data_access/`: parquet and ClickHouse table loading only.
- `src/data_engineering/`: table aggregation and feature construction by `SK_ID_CURR`.
- `src/preprocessing/`: target-safe column selection, imputation, encoding, and train/validation/test splitting.
- `src/models/`: model adapters with a shared `fit`/`predict`/`predict_proba` contract.
- `src/training/`: training, evaluation, artifact persistence, and model selection helpers.
- `src/tuning/`: Optuna objectives and tuning orchestration for local baselines.
- `src/scoring/`: production batch scoring and benchmark timing.
- `scripts/`: thin CLI wrappers only.

## Execution Instructions

### Prerequisites

1. Activate the project virtual environment.
2. Install `04_ml_development/requirements.txt` for validation, EDA, feature engineering, training, tuning, and scoring scripts.
3. Ensure the required local data folders are populated:
   - `data/raw/`
   - `data/dw_parquet/`
4. Configure `.env` and ensure ClickHouse is reachable before using `--source clickhouse`.
5. Build the Docker image before generating profile reports.

### Build the Profile Reports Docker Image

Run the Docker build command from the repository root:

```bash
docker build \
  -f 04_ml_development/src/eda/Dockerfile.profile_reports \
  -t data-architectures-profile-reports:py313 \
  04_ml_development
```

The build context must be `04_ml_development` because the Dockerfile copies the EDA-specific requirements file from `src/eda/requirements.txt`.

### Generate Profile Reports

After building the image, run the profile report wrapper script from the repository root:

```bash
bash 04_ml_development/src/eda/profile_reports.sh
```

By default, the script reads parquet files from `data/dw_parquet/` and writes HTML reports to `data/ml_outputs/profile_reports/`. Both defaults are configured in `04_ml_development/config.yml`.

### Useful Profile Report Commands

Generate reports for selected parquet tables:

```bash
bash 04_ml_development/src/eda/profile_reports.sh --tables rep_bureau rep_application_train
```

Generate sampled reports with a custom sample size:

```bash
bash 04_ml_development/src/eda/profile_reports.sh --sample-size 50000
```

Generate full non-minimal reports:

```bash
bash 04_ml_development/src/eda/profile_reports.sh --full --no-minimal
```

### Build ML Features

Generate the one-row-per-`SK_ID_CURR` feature table from DW parquet outputs:

```bash
python 04_ml_development/scripts/build_features.py --source parquet
```

The output defaults to `data/ml_outputs/features/application_train_features.parquet`.

### Train Models

Train one of the configured model families:

```bash
python 04_ml_development/scripts/train.py --model random_forest
python 04_ml_development/scripts/train.py --model xgboost
python 04_ml_development/scripts/train.py --model local_neural_net
python 04_ml_development/scripts/train.py --model mitra
python 04_ml_development/scripts/train.py --model tabpfn_3
python 04_ml_development/scripts/train.py --model tabpfn_mix
python 04_ml_development/scripts/train.py --model tabicl
python 04_ml_development/scripts/train.py --model pyod_autoencoder
```

Each training run stores a local model bundle under `data/ml_outputs/models/`, metrics under `data/ml_outputs/metrics/`, and MLflow runs under `data/ml_outputs/mlruns/` when MLflow is installed.

### Train Foundation Models with Docker

The three foundation model adapters can also run from one Python 3.13 Docker image. This keeps Mitra compatible with AutoGluon while still supporting TabPFN-3 and TabICL.

Build the image from the repository root:

```bash
docker build \
  -f 04_ml_development/docker/Dockerfile.foundation \
  -t data-architectures-foundation:py313 \
  .
```

Run a quick dependency and CUDA preflight:

```bash
docker run --rm \
  -v "$PWD":/work \
  -w /work \
  data-architectures-foundation:py313 \
  python -c "import torch, tabpfn, tabicl; print(torch.cuda.is_available())"
```

Train a foundation model with the existing CLI:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD":/work \
  -w /work \
  -e TABPFN_TOKEN \
  -e TABPFN_NO_BROWSER=1 \
  data-architectures-foundation:py313 \
  python 04_ml_development/scripts/train.py --model tabicl
```

Repeat the same command with `--model tabpfn_3` or `--model mitra`.

`TABPFN_TOKEN` is required for headless TabPFN runs when the model license has not already been accepted and cached. The image runs on CPU in environments without a visible NVIDIA GPU. To use CUDA, run it on a host with the NVIDIA driver and NVIDIA Container Toolkit configured, and pass GPU access to Docker with `--gpus all`.

### Tune Local Baselines

```bash
python 04_ml_development/scripts/tune.py --model random_forest
python 04_ml_development/scripts/tune.py --model xgboost
python 04_ml_development/scripts/tune.py --model local_neural_net
python 04_ml_development/scripts/tune.py --model tabicl
python 04_ml_development/scripts/tune.py --model tabpfn_mix
python 04_ml_development/scripts/tune.py --model pyod_autoencoder
```

### Evaluate, Score, and Benchmark

Evaluate a saved bundle against the engineered feature table:

```bash
python 04_ml_development/scripts/evaluate.py \
  --model-uri data/ml_outputs/models/random_forest_bundle.joblib
```

Run production-style batch scoring from ClickHouse:

```bash
python 04_ml_development/scripts/batch_score.py \
  --source clickhouse \
  --model-uri data/ml_outputs/models/random_forest_bundle.joblib \
  --limit 1000
```

Use `--source parquet` for local scoring against DW parquet files instead of ClickHouse.

Benchmark several production batch sizes:

```bash
python 04_ml_development/scripts/benchmark_production.py \
  --model-uri data/ml_outputs/models/random_forest_bundle.joblib \
  --batch-sizes 1,10,100,1000
```

Timing metrics include training, validation prediction, test prediction, production transform/predict time, rows per second, and average latency per row.

## Tests

- `python 04_ml_development/tests/test_initial_prep.py`: Validates DW parquet outputs against raw CSV files using the table-specific row slices, excluded columns, and sort columns in `04_ml_development/config.yml`; requires local data in `data/raw/` and `data/dw_parquet/`.
- `python -m pytest 04_ml_development/tests/test_ml_modular_pipeline.py`: Validates parquet loading and filtering, feature construction, target-safe splitting, performance logging, and the PyOD autoencoder adapter.
