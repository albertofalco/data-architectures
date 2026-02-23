import clickhouse_connect
import yaml
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ClickHouse connection details
CH_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CH_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CH_USER = os.getenv("CLICKHOUSE_USER", "default")
CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")

def load_config():
    # Try to load from the project root path first
    config_path = "03_dw_pipeline/src/config.yml"
    if not os.path.exists(config_path):
        # Fallback to local path if running from src folder
        config_path = "config.yml"
        
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def insert_transaction_tables():
    config = load_config()
    staging_db = config["databases"]["staging_db"]
    storage_db = config["databases"]["storage_db"]

    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT, username=CH_USER, password=CH_PASSWORD)
    except Exception as e:
        print(f"Failed to connect to ClickHouse: {e}")
        return

    # Process Option A
    # Option A: Direct insert for tables with PK in source
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

    # Process Option B
    # Option B: Insert with generated row number for tables without PK
    print("Processing Option B inserts...")
    if 'option_b' in config['transaction_tables']:
        for table_info in config['transaction_tables']['option_b']:
            table_name = table_info['name']
            print(f"Inserting into {table_name}...")
            
            # Use rowNumberInAllBlocks() to generate _DW_ID
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

if __name__ == "__main__":
    insert_transaction_tables()
