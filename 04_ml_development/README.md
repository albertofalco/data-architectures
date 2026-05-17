# Module 04: ML Development

## General Description

This module provides the initial machine learning development workspace for the
data architecture pipeline. At this stage, it is focused on validating Data
Warehouse parquet outputs against the original raw CSV files and generating EDA
profile reports from the parquet datasets.

The module consumes downstream outputs produced by the Data Warehouse pipeline:

- **Raw data**: CSV files stored under `data/raw/`
- **DW data**: parquet files stored under `data/dw_parquet/`
- **ML outputs**: reports and artifacts written under `data/ml_outputs/`

The current implementation is validation- and exploration-oriented. It does not
yet provide a package entrypoint or a complete model training pipeline.

## Requirements

Install the module requirements from the repository root after activating the
project virtual environment:

```bash
source venv/bin/activate
python -m pip install -r 04_ml_development/requirements.txt
```

Main dependencies:

- polars
- pyarrow
- pandas
- numpy
- matplotlib
- seaborn
- PyYAML
- tabulate
- fg-data-profiling

### Python Compatibility for Profiling

`fg-data-profiling` is the maintained successor of
`ydata-profiling`/`pandas-profiling`. The package currently lists Python 3.14
support, but its installable package metadata requires Python `<3.14`.

For profile report generation, use Python 3.13 or lower. The Docker-based
profiling workflow uses `python:3.13-slim` to provide a reproducible compatible
runtime.

## Main Functionalities

### DW vs Raw Validation

Compares Data Warehouse parquet outputs against raw CSV source files. The
validation script checks structure, data types, null values, and content using
table-specific rules from `04_ml_development/config.yml`.

### EDA Profile Report Generation

Generates HTML profile reports from DW parquet files using `fg-data-profiling`.
The profiling script supports table selection, sampling, full-file profiling,
and minimal/non-minimal report modes.

### Future ML Development

This section is intentionally lightweight and should be extended as the module
adds feature engineering, training, tuning, evaluation, and production model
artifact workflows.

## Execution Instructions

### Prerequisites

1. Activate the project virtual environment.
2. Install `04_ml_development/requirements.txt` for local validation scripts.
3. Ensure the required local data folders are populated:
   - `data/raw/`
   - `data/dw_parquet/`
4. Build the Docker image before generating profile reports.

### Build the Profile Reports Docker Image

Run the Docker build command from the repository root:

```bash
docker build \
  -f 04_ml_development/src/eda/Dockerfile.profile_reports \
  -t data-architectures-profile-reports:py313 \
  04_ml_development
```

The build context must be `04_ml_development` because the Dockerfile copies the
EDA-specific requirements file from `src/eda/requirements.txt`.

### Generate Profile Reports

After building the image, run the profile report wrapper script from the
repository root:

```bash
bash 04_ml_development/src/eda/profile_reports.sh
```

By default, the script reads parquet files from:

```text
data/dw_parquet/
```

and writes HTML reports to:

```text
data/ml_outputs/profile_reports/
```

Both defaults are configured in `04_ml_development/config.yml`.

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

## Tests and Validation

Run the current DW vs raw validation script from the repository root:

```bash
python 04_ml_development/tests/test_initial_prep.py
```

This validation requires local data in:

- `data/raw/`
- `data/dw_parquet/`

The script uses `04_ml_development/config.yml` to determine table-specific row
slices, excluded columns, and sort columns. It compares raw CSV files against DW
parquet outputs and reports differences in structure, data types, null values,
and content.

## Notes

- `04_ml_development` does not currently expose a package entrypoint. Do not run
  it with `python -m 04_ml_development`.
- Profile report generation should use the Docker workflow to avoid local Python
  version incompatibilities with `fg-data-profiling`.
- Generated reports and local data outputs are written under gitignored data
  directories and should not be committed.
