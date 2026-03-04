# Module 02: Database Connections

## General Description

Python tool to automate data loading from CSV files to a MySQL database, including automatic schema creation, data integrity validation, and synchronization control between files and tables.

## Requirements

- Python 3.8+
- Access to a MySQL server (local or remote)
- MySQL server with database creation permissions
- User must have permissions to create and insert data into the database
- Required libraries:
  - `mysql-connector-python`: MySQL connection
  - `pandas`: CSV reading and processing
  - `numpy`: Numeric data handling
  - `sqlalchemy`: ORM and database abstraction
  - `python-dotenv`: Environment variable management

### MySQL Configuration

Depending on the library used, it may be necessary to enable the `local_infile` option in MySQL:

```sql
-- Check status
SHOW VARIABLES LIKE 'local_infile';

-- Enable (if necessary)
SET GLOBAL local_infile = 1;
```

## Main Functionalities

### CSV to MySQL Loading

The main script (`src/__main__.py`) automates the complete CSV to MySQL data loading process:

1. **Database connection**: Connects to the MySQL server
2. **Database creation**: Creates the database if it does not exist
3. **File detection**: Finds all `.csv` files in the `data/db_input/` folder
4. **Automatic table creation**: Infers data types and creates tables

### Data Processing with SQLAlchemy

For each `.csv` file in `data/db_input/`, reading is performed using the **Pandas** library and **SQLAlchemy** engine.

The import process:
- Analyzes the data type of each column
- Converts `np.nan` and `None` values to compatible `NULL` format
- Creates the table if it does not exist
- Deletes existing records if the table already exists (TRUNCATE)
- Ignores the first row (headers)

## Module Structure

```
02_database_connections/
├── src/
│   ├── __main__.py                 # Main loading script
│   └── ...
├── tests/
│   ├── test_db_connection.py       # Connectivity verification
│   ├── test_table_names.py         # Synchronization validation
│   ├── test_integrity.py           # Integrity verification
│   └── __init__.py
├── data/
│   └── db_input/                   # CSV data folder
├── requirements.txt                # Dependencies
└── README.md                       # This file
```

## Execution Instructions

### Installation

1. Clone or download this repository
2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r 02_database_connections/requirements.txt
```

### Data Preparation

Place CSV files in the `data/db_input/` folder:

```
02_database_connections/
...
data/
└── db_input/
    ├── application_train.csv
    ├── bureau.csv
    └── ...
```

**CSV Requirements:**
- File must have `.csv` extension
- First row must contain column names (headers)
- Values must be comma-separated (`,`)
- Text values must be quoted (`"`)

### Connection Configuration

The script obtains database access credentials from the `.env` file located in the repository root.

```
01_data_normalization/
02_database_connections/
data/
...
.env
```

The `.env` file has the following structure:

```bash
DB_HOST=localhost
DB_USER=user
DB_PASSWORD=password
DB_NAME=example
```

The script also supports passing arguments via terminal:

```bash
python -m 02_database_connections --host localhost --user user --password password --database example
```

Once the MySQL server connection is configured, it creates the database DB_NAME if it does not exist.

### Security Considerations

1. **Passwords**: Do not pass passwords on the command line in production
   - Use environment variables: `$DB_PASSWORD`
   - Or use encrypted configuration files

2. **MySQL Permissions**: Create user with limited permissions
   ```sql
   CREATE USER 'datos_user'@'localhost' IDENTIFIED BY 'password';
   GRANT CREATE, DROP, INSERT, SELECT, UPDATE ON database_name.* TO 'datos_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

### Limitations and Considerations

| Aspect | Limitation | Solution |
|--------|-----------|----------|
| Data types | Only INT, FLOAT, TEXT | Use SQLAlchemy + SQLTypes |
| CSV size | Depends on RAM | Process in chunks |
| Features | Does not support indexes/relations | Create schema post-load |
| Load errors | Stops on first error | Implement partial rollback |

### Troubleshooting

#### Error: "Access denied for user"
- Verify credentials (host, user, password)
- Ensure the user exists in MySQL

#### Error: "LOAD DATA LOCAL INFILE access denied"
- Enable `local_infile` on the server
- Verify user's `FILE` permissions

#### Error: "Table already exists"
- The script uses `CREATE TABLE IF NOT EXISTS`, so this should not occur
- If it occurs, verify write permissions

#### Error: "No such file or directory"
- Verify that the `data/db_input/` folder exists
- Ensure you are in the correct directory

### Usage Example

```bash
python -m 02_database_connections
```

## Tests

The module includes three test suites to validate different aspects of data connection and loading.

### test_db_connection.py

Verifies database connectivity using two different methods:

- `mysql-connector-python`: Native MySQL connection
- `SQLAlchemy`: ORM with MySQL driver

**Execution:**
```bash
python -m tests.test_db_connection
# Alternative option:
python tests/test_db_connection.py
```

### test_table_names.py

Validates synchronization between available CSV files and existing tables in the MySQL database:
- Verifies that all CSVs have corresponding tables
- Detects CSV files that have not been loaded yet
- Finds orphan tables (without source CSV file)
- Data quality audit

**Execution:**
```bash
python -m 02_database_connections.tests.test_table_names
# Alternative option (with arguments):
python tests/test_table_names.py --host 127.0.0.1 --user user --password password --database example
```

### test_integrity.py

Table content control by verifying integrity against source files:
- **Table name validation**: Compares DB tables vs CSV files
- **Structure (shape) validation**: Verifies that rows and columns match
- **Schema validation**: Checks column names and order
- **Content comparison**: Cell-by-cell validation with decimal tolerance

**Execution:**
```bash
python -m 02_database_connections.tests.test_integrity
# Alternative option (with arguments):
python 02_database_connections/tests/test_integrity.py --host 127.0.0.1 --user user --password password --database example
```
