"""Diagnose ClickHouse connectivity to MySQL through the MySQL engine."""

# ==================== IMPORTS ====================

import os

import clickhouse_connect
from dotenv import load_dotenv

# ==================== CONFIGURATION ====================

# Load environment variables.
load_dotenv()

TEMP_DB = "test_mysql_engine_connection"


# ==================== HELPER FUNCTIONS ====================

def sql_string(value):
    """Escape a value for use as a ClickHouse string literal."""
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def masked(value):
    """Mask a credential for diagnostic output."""
    if not value:
        return ""
    return "*" * 8


def get_clickhouse_config():
    """Return ClickHouse connection settings from environment variables."""
    host = os.getenv("CLICKHOUSE_HOST", "localhost")
    try:
        port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    except ValueError:
        port = 8123

    user = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "")

    return host, port, user, password


def get_mysql_config():
    """Return the MySQL settings used by the ClickHouse MySQL engine."""
    host = os.getenv("MYSQL_HOST_FOR_CH", "host.docker.internal")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "mysql-clickhouse")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DB", "data_arch_prod")

    return host, port, user, password, database


# ==================== MAIN FUNCTIONS ====================

def test_connection_mysql_from_dw():
    """Test MySQL access through a temporary ClickHouse MySQL database."""
    ch_host, ch_port, ch_user, ch_password = get_clickhouse_config()
    mysql_host, mysql_port, mysql_user, mysql_password, mysql_database = get_mysql_config()

    print(f"Connecting to ClickHouse at {ch_host}:{ch_port} as {ch_user}...")
    print(
        "Testing MySQL engine connection to "
        f"{mysql_host}:{mysql_port}/{mysql_database} as {mysql_user} "
        f"with password {masked(mysql_password)}..."
    )

    client = None

    try:
        client = clickhouse_connect.get_client(
            host=ch_host,
            port=ch_port,
            username=ch_user,
            password=ch_password,
        )
        print("ClickHouse connection successful!")

        client.command(f"DROP DATABASE IF EXISTS {TEMP_DB}")

        create_query = f"""
        CREATE DATABASE {TEMP_DB}
        ENGINE = MySQL(
            '{sql_string(mysql_host)}:{sql_string(mysql_port)}',
            '{sql_string(mysql_database)}',
            '{sql_string(mysql_user)}',
            '{sql_string(mysql_password)}'
        )
        """
        client.command(create_query)
        print(f"Temporary database {TEMP_DB} created with MySQL engine.")

        print("\nMySQL tables visible from ClickHouse:")
        result = client.query(f"SHOW TABLES FROM {TEMP_DB}")
        if result.result_rows:
            for row in result.result_rows:
                print(f"- {row[0]}")
        else:
            print("- No tables found.")

        print("\nClickHouse to MySQL connection successful!")

    except Exception as e:
        print(f"Connection failed: {e}")

    finally:
        if client is not None:
            try:
                client.command(f"DROP DATABASE IF EXISTS {TEMP_DB}")
                print(f"Temporary database {TEMP_DB} dropped.")
            except Exception as cleanup_error:
                print(f"Cleanup failed: {cleanup_error}")


# ==================== EXECUTION ====================

if __name__ == "__main__":
    test_connection_mysql_from_dw()
