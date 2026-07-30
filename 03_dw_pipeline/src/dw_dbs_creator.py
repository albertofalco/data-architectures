"""Create the required ClickHouse staging and storage databases."""

# ==================== IMPORTS ====================

import clickhouse_connect
import yaml
import os
from dotenv import load_dotenv

# ==================== CONFIGURATION ====================

# Load environment variables.
load_dotenv()

# ClickHouse connection settings.
CH_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CH_PORT = os.getenv("CLICKHOUSE_PORT", "8123")
CH_USER = os.getenv("CLICKHOUSE_USER", "default")
CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")

# MySQL settings used by the ClickHouse MySQL engine.
MYSQL_HOST = os.getenv("MYSQL_HOST_FOR_CH", "host.docker.internal")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "mysql-clickhouse")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "data_arch_prod")

# ==================== HELPER FUNCTIONS ====================

def load_config():
    """Load the pipeline configuration from YAML."""
    with open("03_dw_pipeline/src/config.yml", "r") as f:
        return yaml.safe_load(f)

# ==================== MAIN FUNCTIONS ====================

def create_databases():
    """Create missing staging and storage databases in ClickHouse."""
    config = load_config()
    staging_db = config["databases"]["staging_db"]
    storage_db = config["databases"]["storage_db"]

    client = clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT, username=CH_USER, password=CH_PASSWORD)

    # Create the MySQL-backed staging database when it is missing.
    print(f"Checking database {staging_db}...")
    exists = client.command(f"EXISTS DATABASE {staging_db}")
    if exists:
        print(f"Database {staging_db} already exists.")
    else:
        print(f"Creating database {staging_db}...")
        query = f"""
        CREATE DATABASE {staging_db}
        ENGINE = MySQL('{MYSQL_HOST}:{MYSQL_PORT}', '{MYSQL_DB}', '{MYSQL_USER}', '{MYSQL_PASSWORD}')
        """
        client.command(query)
        print(f"Database {staging_db} created.")

    # Create the storage database when it is missing.
    print(f"Checking database {storage_db}...")
    exists = client.command(f"EXISTS DATABASE {storage_db}")
    if exists:
        print(f"Database {storage_db} already exists.")
    else:
        print(f"Creating database {storage_db}...")
        client.command(f"CREATE DATABASE {storage_db}")
        print(f"Database {storage_db} created.")

# ==================== EXECUTION ====================

if __name__ == "__main__":
    create_databases()
