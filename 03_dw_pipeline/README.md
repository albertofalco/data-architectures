# Module 03: Data Warehouse Pipeline

## Objective

This module implements a complete Data Warehouse pipeline that creates and populates a dimensional data warehouse using ClickHouse as the analytical database. The pipeline connects to a MySQL staging database (via ClickHouse's MySQL engine) and creates an optimized storage layer with transactional tables, dictionaries, and materialized views for reporting.

The module follows a star schema design pattern where:
- **Staging layer**: Connects directly to MySQL via ClickHouse MySQL engine
- **Storage layer**: Contains normalized transactional tables using MergeTree engine
- **Dictionary layer**: Provides lookup mappings from IDs to descriptions
- **Reporting layer**: Denormalized tables (rep_*) with descriptions instead of IDs, powered by materialized views

## Requirements

- clickhouse-connect
- pandas
- PyYAML
- SQLAlchemy
- mysql-connector-python
- python-dotenv
- pytest

## Main Functionalities

### Database Creation
Creates two databases in ClickHouse:
- **Staging database**: Uses MySQL engine to connect directly to the source MySQL database
- **Storage database**: Standard ClickHouse database for storing processed data

### Dictionary Creation
Creates ClickHouse dictionaries from dimension tables (dim_*) in the staging database. These dictionaries provide fast lookups to replace ID columns with descriptive values.

### Transactional Table Creation
Creates transactional (fact) tables in the storage database with two options:
- **Option A**: Tables with defined primary keys (SK_ID columns)
- **Option B**: Tables without primary keys (adds _DW_ID column)

### Report Table Creation
Creates denormalized report tables (rep_*) that replace ID columns with their corresponding descriptions using ClickHouse dictionaries. Each report table is powered by a materialized view (mv_*) that automatically populates the table.

### Data Insertion
Inserts data from staging tables into storage transactional tables, and automatically populates report tables through materialized views.

## Execution Instructions

### Prerequisites
1. MySQL database running with normalized data
2. ClickHouse server running
3. Environment variables configured (.env file)

Run all commands from the repository root. Activate the project virtual environment and install the module dependencies before executing the pipeline:

```bash
source venv/bin/activate
python -m pip install -r 03_dw_pipeline/requirements.txt
```

### Environment Variables Required
```
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=********
MYSQL_HOST_FOR_CH=host.docker.internal
MYSQL_PORT=3306
MYSQL_USER=mysql-clickhouse
MYSQL_PASSWORD=********
MYSQL_DB=data_arch_prod
```

### Execution Order

1. **Create databases**:
    ```bash
    python -m 03_dw_pipeline.src.dw_dbs_creator
    ```

2. **Create dictionaries**:
    ```bash
    python -m 03_dw_pipeline.src.dw_dict_creator
    ```

3. **Create transactional tables**:
    ```bash
    python -m 03_dw_pipeline.src.dw_tran_creator
    ```

4. **Insert data into transactional tables**:
    ```bash
    python -m 03_dw_pipeline.src.dw_tran_insert
    ```

5. **Create materialized views and report tables**:
    ```bash
    python -m 03_dw_pipeline.src.dw_mv_creator
    ```

6. **Insert data into materialized views**:
    ```bash
    python -m 03_dw_pipeline.src.dw_mv_insert
    ```

## Tests

- `test_connection_dw.py`: Tests the connectivity to ClickHouse server. Validations performed:
    - **Connection**: Verifies that credentials are correct and ClickHouse server is accessible
    - **Database listing**: Lists all available databases in the server
- `test_connection_mysql_from_dw.py`: Diagnostically verifies that ClickHouse can connect to MySQL through the MySQL engine, lists the visible MySQL tables, and removes the temporary ClickHouse database after the check.
- `test_raw_dw.py`: Verifies data integrity between CSV source files and report tables in ClickHouse. Validations performed:
    - **Row count**: Verifies that the number of rows in CSV matches the database table
    - **Columns**: Validates that all expected columns are present
    - **Content**: Compares data values between CSV and database table (with tolerance of 1e-5 for numerical precision)
    - **Filtering**: Applies filtering rules for datasets with excluded entries
    - **Configuration**: Supports excluded columns and reference columns for ordering and filtering
    - **Large datasets**: Uses chunk-based processing
    - **Null handling**: Normalizes NaN and None values before comparison
