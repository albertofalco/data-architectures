"""Load staging data into ClickHouse transaction tables."""

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
CH_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CH_USER = os.getenv("CLICKHOUSE_USER", "default")
CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")

# ==================== HELPER FUNCTIONS ====================

def load_config():
    """Load the pipeline configuration from YAML."""
    # Prefer the configuration path relative to the project root.
    config_path = "03_dw_pipeline/src/config.yml"
    if not os.path.exists(config_path):
        # Fall back to a path relative to this module.
        config_path = "config.yml"
        
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# ==================== MAIN FUNCTIONS ====================

def insert_transaction_tables():
    """Load all configured transaction tables from staging."""
    config = load_config()
    staging_db = config["databases"]["staging_db"]
    storage_db = config["databases"]["storage_db"]

    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT, username=CH_USER, password=CH_PASSWORD)
    except Exception as e:
        print(f"Failed to connect to ClickHouse: {e}")
        return

    # Load option A tables directly because they have source primary keys.
    print("Processing Option A inserts...")
    if 'option_a' in config['transaction_tables']:
        for table_info in config['transaction_tables']['option_a']:
            table_name = table_info['name']
            print(f"Inserting into {table_name}...")
            
            insert_query = f"""
            INSERT INTO {storage_db}.{table_name}
            SELECT * FROM {staging_db}.{table_name}
            """
            try:
                client.command(insert_query)
                print(f"Successfully inserted data into {storage_db}.{table_name}")
            except Exception as e:
                print(f"Error inserting into {table_name}: {e}")

    # Load option B tables with synthetic identifiers.
    print("Processing Option B inserts...")
    if 'option_b' in config['transaction_tables']:
        for table_info in config['transaction_tables']['option_b']:
            table_name = table_info['name']
            print(f"Inserting into {table_name}...")
            
            # Generate _DW_ID values with rowNumberInAllBlocks().
            insert_query = f"""
            INSERT INTO {storage_db}.{table_name}
            SELECT rowNumberInAllBlocks(), *
            FROM {staging_db}.{table_name}
            """
            try:
                client.command(insert_query)
                print(f"Successfully inserted data into {storage_db}.{table_name}")
            except Exception as e:
                print(f"Error inserting into {table_name}: {e}")

# ==================== EXECUTION ====================

if __name__ == "__main__":
    insert_transaction_tables()
