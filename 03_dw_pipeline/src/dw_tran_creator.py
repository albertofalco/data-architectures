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
    with open("03_dw_pipeline/src/config.yml", "r") as f:
        return yaml.safe_load(f)

def get_table_columns(client, database, table):
    query = f"""
    SELECT name, type
    FROM system.columns
    WHERE database = '{database}' AND table = '{table}'
    ORDER BY position
    """
    result = client.query(query)
    return [{'name': row[0], 'type': row[1]} for row in result.result_rows]

def create_transaction_tables():
    config = load_config()
    staging_db = config["databases"]["staging_db"]
    storage_db = config["databases"]["storage_db"]

    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT, username=CH_USER, password=CH_PASSWORD)
    except Exception as e:
        print(f"Failed to connect to ClickHouse: {e}")
        return

    # Process Option A
    # Option A: Tables with PRIMARY KEY restriction created in the mysql database.
    print("Processing Option A tables...")
    for table_info in config['transaction_tables']['option_a']:
        table_name = table_info['name']
        print(f"Creating table {table_name}...")
        
        columns = get_table_columns(client, staging_db, table_name)
        if not columns:
            print(f"Warning: Table {table_name} not found in {staging_db}. Skipping.")
            continue
            
        col_defs = ", ".join([f"{col['name']} {col['type']}" for col in columns])
        
        # Detect Primary Keys: All columns starting with 'SK_ID'
        pk_cols = [col['name'] for col in columns if col['name'].startswith('SK_ID')]
        
        if not pk_cols:
            # Fallback to first column if no SK_ID found (though unexpected for Option A)
            print(f"Warning: No 'SK_ID' columns found for {table_name}. Using first column as PK.")
            pk_col_str = columns[0]['name']
        else:
            pk_col_str = ", ".join(pk_cols)
        
        create_query = f"""
        CREATE TABLE IF NOT EXISTS {storage_db}.{table_name}
        ({col_defs})
        ENGINE = MergeTree()
        ORDER BY ({pk_col_str})
        SETTINGS allow_nullable_key = 1
        """
        try:
            client.command(create_query)
            print(f"Table {storage_db}.{table_name} created with PK: ({pk_col_str}).")
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")

    # Process Option B
    # Option B: Tables without PRIMARY KEY restriction created in the mysql database.
    print("Processing Option B tables...")
    for table_info in config['transaction_tables']['option_b']:
        table_name = table_info['name']
        print(f"Creating table {table_name}...")
        
        columns = get_table_columns(client, staging_db, table_name)
        if not columns:
            print(f"Warning: Table {table_name} not found in {staging_db}. Skipping.")
            continue
            
        col_defs = ", ".join([f"{col['name']} {col['type']}" for col in columns])
        
        # Add _DW_ID column
        create_query = f"""
        CREATE TABLE IF NOT EXISTS {storage_db}.{table_name}
        (
            _DW_ID UInt64,
            {col_defs}
        )
        ENGINE = MergeTree()
        ORDER BY _DW_ID
        """
        try:
            client.command(create_query)
            print(f"Table {storage_db}.{table_name} created.")
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")

if __name__ == "__main__":
    create_transaction_tables()
