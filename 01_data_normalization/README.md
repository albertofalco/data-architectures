# Module 01: Data Normalization

## General Description

This module performs complete normalization of multiple datasets applying relational database design principles (1NF, 2NF, 3NF) and resolving shared dimension overlaps between related datasets.

## Requirements

- pandas
- numpy
- pandasql
- pytest (optional)

## Main Features

### Features of the normalization process

- Normalization of datasets to eliminate redundancy and improve data integrity
- Creation of reference tables for categorical attributes
- Correction of overlapping shared dimension between several datasets (e.g. `dim_name_contract_type`, `dim_weekday_appr_process_start`, `dim_name_type_suite`).

### Sequential phases

- **Phase 1: Normalization of Individual Datasets**
  - Processes datasets stored in /data/raw (`application_train`, `application_test`, `bureau_balance`, `bureau`, `credit_card_balance`, `installments_payments`, `POS_CASH_balance`, `previous_application`)
  - Resolves the atomization of `ORGANIZATION_TYPE`: extracts type number into separate column and creates `ORGANIZATION_TYPE_2` attribute
  - Optimizes datasets by replacing categorical values with IDs
  - Dimension tables in separate CSV files
- **Phase 2: Corrections for Datasets with Dimension Overlaps**
  - Since the mapping performed by pandas automatically assigns values according to the order in which they occur along each attribute, ID remappings are applied to align shared dimensions (e.g. `NAME_CONTRACT_TYPE`, `WEEKDAY_APPR_PROCESS_START`, `NAME_TYPE_SUITE`) across datasets to ensure consistency.
- **Phase 3: Cleanup**
  - Removes temporary directories and redundant files.

## Module Structure

### Module directory structure

```
01_data_normalization/
├── notebooks/
│   └── ...
├── src/
│   ├── __main__.py
│   └── ...
├── tests/
│   ├── test_content.py
│   ├── test_data_types.py
│   ├── test_head_csv.py
│   ├── test_structure.py
│   └── ...
└── utils/
    ├── common_dims_mapper.py
    ├── mappings.json
    ├── schema_report.csv
    ├── schema_report.py
    └── ...
```

### Expected input and output directory structure

```
data/
├── raw/
│   ├── application_train.csv
│   └── ...
├── db_input/
│   ├── application_train/
│   │   └── ...
│   ├── common_dims/
│   │   └── ...
│   └── ...
└── ...
```

## Execution Instructions

### Options to run the main script

```bash
# Run directly.
python 01_data_normalization/src/__main__.py
# Or as a module.
python -m 01_data_normalization
```

### Important Notes

1. The script expects input CSVs in `../data/raw/`
2. Output files are saved in `../data/db_input/`
3. Temporary directories are automatically cleaned up at the end

## Tests

### Overview of tests

- `test_content.py`: Main script that verifies normalized datasets maintain data integrity by comparing them with originals. Validations performed include structure, columns, and content.
- `test_data_types.py`: Ensures data types of columns are consistent between original and normalized datasets.
- `test_head_csv.py`: Checks that the first few rows of normalized datasets match the original datasets to confirm correct transformations.
- `test_structure.py`: Validates that the normalized datasets adhere to the expected structure (e.g. correct number of columns, presence of reference tables).

### Notes on Validations

- Columns `ORGANIZATION_TYPE` and `ORGANIZATION_TYPE_2` are excluded from comparison as they are transformed during normalization
- A maximum difference of `1e-5` in numeric values is tolerated to allow for rounding errors
- The script generates a detailed summary of differences found to facilitate debugging
