# Module 01: Data Normalization

## General Description

This module performs complete normalization of multiple datasets applying relational database design principles (1NF, 2NF, 3NF) and resolving shared dimension overlaps between related datasets.

## Requirements

- pandas
- numpy
- pandasql
- pytest (optional)

## Main Functionalities

### Standard Normalization
- Data atomization (First Normal Form - 1NF)
- Table decomposition into dimensions
- Creation of reference tables (lookup tables)

### Overlap Correction
Identifies and resolves inconsistencies in the 3 shared dimension tables between `application_train` and `previous_application`:
- `dim_name_contract_type`
- `dim_weekday_appr_process_start`
- `dim_name_type_suite`

## Phase Processing

The main script executes three sequential phases:

### Phase 1: Normalization and Design Optimization
Processes datasets stored in db_input:
- `application_train.csv`
- `application_test.csv`
- `bureau_balance.csv`
- `bureau.csv`
- `credit_card_balance.csv`
- `installments_payments.csv`
- `POS_CASH_balance.csv`
- `previous_application.csv`

The following transformations are performed:
- Atomization of `ORGANIZATION_TYPE`: extracts type number into separate column and creates `ORGANIZATION_TYPE_2` attribute
- Optimizes datasets by replacing categorical values with IDs. Each categorical attribute is decomposed into:
  - Main Table: Contains only IDs (dimension references)
  - Dimension Table: Mapping of ID → Original value
- Dimension tables in separate CSV files

### Phase 2: Corrections for Datasets with Dimension Overlaps
Two datasets share some common dimensions:
- `application_train.csv`
- `previous_application.csv`

Since the mapping performed by pandas automatically assigns values according to the order in which they occur along each attribute, ID remappings are applied to align shared dimensions:

**For `application_train`:**
- `NAME_CONTRACT_TYPE_ID`: Mapping of 2 categories
- `WEEKDAY_APPR_PROCESS_START_ID`: Mapping of 7 days (1 - MONDAY to 7 - SUNDAY)
- `NAME_TYPE_SUITE_ID`: Mapping of 7 types

**For `previous_application`:**
- `WEEKDAY_APPR_PROCESS_START_ID`: Mapping of 7 days

Exports:
- Corrected datasets
- Three common dimension tables reconciled with reference datasets

### Phase 3: Cleanup
Removes temporary directories from original `application_train` and `previous_application`.

## Module Structure

```
data/db_input/
├── application_test/
│   ├── application_test.csv
│   ├── dim_*.csv
│   └── ...
├── bureau/
│   ├── bureau.csv
│   ├── dim_*.csv
│   └── ...
├── common_dims/
│   ├── dim_name_contract_type.csv
│   ├── dim_weekday_appr_process_start.csv
│   └── dim_name_type_suite.csv
└── ...
```

## Execution Instructions

Run as script:

```bash
python 01_data_normalization/src/__main__.py
```

Or run as module:

```bash
python -m 01_data_normalization
```

### Important Notes

1. The script expects input CSVs in `../data/raw/`
2. Output files are saved in `../data/db_input/`
3. Temporary directories are automatically cleaned up at the end

## Tests

### test_content.py

Main script that verifies normalized datasets maintain data integrity by comparing them with originals.

**Datasets reviewed:**
- `application_train`
- `bureau`
- `previous_application`

**Validations performed:**
1. **Structure**: Verifies row count is maintained
2. **Columns**: Validates all expected columns are present
3. **Content**: Compares values between original and normalized datasets

### Test Execution

Run directly:

```bash
python 01_data_normalization/tests/test_content.py
```

Or as module:

```bash
python -m 01_data_normalization.tests.test_content
```

### Notes on Validations

- Columns `ORGANIZATION_TYPE` and `ORGANIZATION_TYPE_2` are excluded from comparison as they are transformed during normalization
- A maximum difference of `1e-5` in numeric values is tolerated to allow for rounding errors
- The script generates a detailed summary of differences found to facilitate debugging
