# Module 01: Data Normalization

## Objective

This module performs complete normalization of multiple datasets applying relational database design principles (1NF, 2NF, 3NF) and resolving shared dimension overlaps between related datasets.

## Requirements

- pandas
- numpy
- pandasql
- ipykernel
- ipython
- jupyter_client
- jupyter_core
- ipython_pygments_lexers

## Main Functionalities

### Features of the normalization process

- Normalization of datasets to eliminate redundancy and improve data integrity
- Creation of reference tables for categorical attributes
- Correction of overlapping shared dimension between several datasets (e.g. `dim_name_contract_type`, `dim_weekday_appr_process_start`, `dim_name_type_suite`).

### Sequential phases

- **Phase 1: Normalization of Individual Datasets**
  - Processes datasets stored in `data/raw/` (`application_train`, `bureau_balance`, `bureau`, `credit_card_balance`, `installments_payments`, `POS_CASH_balance`, `previous_application`)
  - Resolves the atomization of `ORGANIZATION_TYPE`: extracts type number into separate column and creates `ORGANIZATION_TYPE_2` attribute
  - Optimizes datasets by replacing categorical values with IDs
  - Dimension tables in separate CSV files
- **Phase 2: Corrections for Datasets with Dimension Overlaps**
  - Since the mapping performed by pandas automatically assigns values according to the order in which they occur along each attribute, ID remappings are applied to align shared dimensions (e.g. `NAME_CONTRACT_TYPE`, `WEEKDAY_APPR_PROCESS_START`, `NAME_TYPE_SUITE`) across datasets to ensure consistency.

## Execution Instructions

### Options to run the main script

Run all commands from the repository root. Activate the project virtual environment and install the module dependencies first:

```bash
source venv/bin/activate
python -m pip install -r 01_data_normalization/requirements.txt
```

```bash
# Run directly.
python 01_data_normalization/src/__main__.py
# Or as a module.
python -m 01_data_normalization
```

### Important Notes

1. The script expects input CSVs in `data/raw/`
2. Output files are saved in `data/db_input/`

## Tests

- `test_content.py`: Main script that verifies normalized datasets maintain data integrity by comparing them with originals. Validations performed include structure, columns, and content.
  - Excludes `ORGANIZATION_TYPE` and `ORGANIZATION_TYPE_2` because normalization transforms them.
  - Tolerates numeric differences below `1e-5` to account for rounding.
  - Prints a detailed summary of detected differences.
- `test_data_types.py`: Analyzes up to 10,000 rows from each normalized CSV, flags ID columns that are not `int64` or nullable `Int64`, and writes the results to `01_data_normalization/tests/data_types.csv`.
- `test_head_csv.py`: Prints the first 20 `HOUSETYPE_MODE_ID` values from the normalized `application_train/application_train.csv` file for manual inspection.
- `test_structure.py`: Validates that the normalized datasets adhere to the expected structure (e.g. correct number of columns, presence of reference tables).
