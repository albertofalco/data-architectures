# data-architectures

Data Architectures for Risk Management and Audit

## Modules

### 01_data_normalization

**Description:** Normalizes datasets applying relational database design principles (1NF, 2NF, 3NF), including atomization of values, creation of dimension tables, and resolution of shared dimension overlaps.

**Main script:** [`src/__main__.py`](01_data_normalization/src/__main__.py)

**Main functionalities:**
- Standard Normalization: Data atomization (First Normal Form - 1NF), table decomposition into dimensions, and creation of reference/lookup tables
- Overlap Correction: Identifies and resolves inconsistencies in 3 shared dimension tables between `application_train` and `previous_application` (dim_name_contract_type, dim_weekday_appr_process_start, dim_name_type_suite)
- Phase Processing: Three sequential phases (1. Normalization and design optimization, 2. Corrections for dimension overlaps, 3. Cleanup of temporary directories)
- Atomization of ORGANIZATION_TYPE with creation of ORGANIZATION_TYPE_2 attribute
- Export of normalized datasets and dimension tables as CSV files

**Tests:**
- `test_content.py`: Validates content integrity by comparing normalized datasets with originals, verifying structure (shape), columns, and values for datasets like `application_train`, `bureau`, and `previous_application`

---

### 02_database_connections

**Description:** Python tool to automate data loading from CSV files to a MySQL database, with automatic schema creation, data integrity validation, and synchronization control.

**Main script:** [`src/__main__.py`](02_database_connections/src/__main__.py)

**Main functionalities:**
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

**Main functionalities:**
- Database creation: Staging database uses MySQL engine for direct connection to source; storage database uses standard ClickHouse
- Dictionary creation: Creates ClickHouse dictionaries from dimension tables for fast lookups
- Transactional table creation: Two options - Option A (tables with defined PK from SK_ID columns) and Option B (tables without PK, adds _DW_ID column)
- Report table creation: Denormalized tables (rep_*) that replace IDs with descriptions using ClickHouse dictionaries, powered by materialized views (mv_*)

**Tests:**
- `test_connection_dw.py`: Verifies ClickHouse connectivity and lists available databases
- `test_raw_dw.py`: Verifies data integrity between CSV source files and report tables in ClickHouse, validating row count, columns, and content

---

### 04_ml_development

**Description:** Machine Learning development module (in development). Currently provides data validation utilities to compare raw CSV data with Data Warehouse parquet files.

**Main script:** [`tests/initial_prep.py`](04_ml_development/tests/initial_prep.py)

**Main functionalities:**
- Data comparison between raw CSV files and Data Warehouse parquet files using Polars
- Structure validation (shape, columns)
- Data type validation
- Content comparison with configurable float tolerance
- Export of differences to CSV files

**Tests:**
- `initial_prep.py`: Compares Polars DataFrames and exports differences to CSV files for analysis
