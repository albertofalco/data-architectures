# Module 02: Database Connections

## Objective

Python module to automate data loading from CSV files to a MySQL database, including automatic schema creation, data integrity validation, and synchronization control between files and tables.

## Requirements

- Python 3.10+
- Access to a MySQL server (local or remote)
- MySQL server with database creation permissions
- User must have permissions to create and insert data into the database
- Required libraries:
  - `mysql-connector-python`: MySQL connection
  - `pandas`: CSV reading and processing
  - `numpy`: Numeric data handling
  - `sqlalchemy`: ORM and database abstraction
  - `python-dotenv`: Environment variable management
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
- Replaces the table if it already exists by using `to_sql(..., if_exists="replace")`
- Ignores the first row (headers)

## Execution Instructions

### Installation

Run all commands from the repository root.

1. Clone or download this repository
2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   python -m pip install -r 02_database_connections/requirements.txt
   ```

### Data Preparation

Place CSV files in the `data/db_input/` folder.

### Connection Configuration

The script obtains database access credentials from the `.env` file located in the repository root.

The `.env` file has the following structure:

```bash
DB_HOST=localhost
DB_USER=user
DB_PASSWORD=password
DB_NAME=example
```

The script also supports passing arguments via terminal:

```bash
python -m 02_database_connections --host localhost --user user --password --database example
```

Once the MySQL server connection is configured, it creates the database DB_NAME if it does not exist.

### Troubleshooting

- **Error: "Access denied for user"**
   - Verify credentials (host, user, password)
   - Ensure the user exists in MySQL
- **Error: "No such file or directory"**
   - Verify that the `data/db_input/` folder exists
   - Ensure you are in the correct directory

## Tests

The module includes six diagnostic and validation scripts for different aspects of database connectivity and data loading.

- `test_db_connection.py`: Verifies database connectivity using two different methods:
   - `mysql-connector-python`: Native MySQL connection
   - `SQLAlchemy`: ORM with MySQL driver
- `test_int_size.py`: Evaluates whether columns in the CSV files require `BigInteger`:
   - Analyzes every CSV file in the input directory
   - Verifies whether numeric columns contain values that exceed the range of a 32-bit integer
   - Reports identified columns as candidates for `BigInteger` in the database
- `test_dbinput_db.py`: Verifies normalized CSV content against the corresponding MySQL tables:
   - Table name validation: Compares DB tables vs CSV files
   - Structure (shape) validation: Verifies that rows and columns match
   - Schema validation: Checks column names and order
   - Content comparison: Cell-by-cell validation with decimal tolerance
- `test_dbinput_debug.py`: Investigates isolated CSV-to-MySQL discrepancies using a configurable sample:
   - Selects a manageable subset using configured primary keys
   - Supports exporting detected differences to a local CSV file
- `test_raw_db.py`: Validates the integrity and structure of the raw database:
   - Allows using chunks for comparing content.
- `test_table_names.py`: Validates synchronization between available CSV files and existing tables in the MySQL database:
   - Verifies that all CSVs have corresponding tables
   - Detects CSV files that have not been loaded yet
   - Finds orphan tables (without source CSV file)
   - Data quality audit
