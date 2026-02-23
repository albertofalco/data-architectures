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
    query = f"DESCRIBE TABLE {database}.{table}"
    try:
        result = client.query(query)
        return [{'name': row[0], 'type': row[1]} for row in result.result_rows]
    except Exception as e:
        print(f"Error getting columns for {table}: {e}")
        return []

def get_dictionaries(client, database):
    query = f"SHOW DICTIONARIES FROM {database}"
    result = client.query(query)
    return set([row[0] for row in result.result_rows])

def get_dictionary_columns(client, database, dict_name):
    query = f"DESCRIBE {database}.{dict_name}"
    result = client.query(query)
    return [{'name': row[0], 'type': row[1]} for row in result.result_rows]

def find_matching_dict(col_name, dict_names):
    if col_name.upper().endswith("_ID"):
        base = col_name[:-3].lower()
        candidate = f"dict_dim_{base}"
        if candidate in dict_names:
            return candidate
    return None

def insert_data():
    config = load_config()
    storage_db = config["databases"]["storage_db"]

    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT, username=CH_USER, password=CH_PASSWORD)
    except Exception as e:
        print(f"Failed to connect to ClickHouse: {e}")
        return

    dict_names = get_dictionaries(client, storage_db)
    
    all_tables = config['transaction_tables']['option_a'] + config['transaction_tables']['option_b']
    
    for t in all_tables:
        table_name = t['name']
        print(f"Generating INSERT query for {table_name} -> rep_{table_name}...")
        
        src_cols = get_table_columns(client, storage_db, table_name)
        if not src_cols:
            print(f"Skipping {table_name} (source not found).")
            continue

        select_parts = []
        
        for col in src_cols:
            col_name = col['name']
            
            matching_dict = find_matching_dict(col_name, dict_names)
            
            if matching_dict:
                dict_cols = get_dictionary_columns(client, storage_db, matching_dict)
                desc_col = None
                for dc in dict_cols:
                    if dc['name'] != col_name and not dc['name'].endswith('_ID'):
                        desc_col = dc
                        break
                
                # Fallback
                if not desc_col and len(dict_cols) > 1:
                    desc_col = dict_cols[1]
                
                if desc_col:
                    desc_name = desc_col['name']
                    select_parts.append(f"dictGet('{storage_db}.{matching_dict}', '{desc_name}', {col_name})")
                else:
                    select_parts.append(col_name)
            else:
                select_parts.append(col_name)

        # Build and Execute Query
        # Using INSERT INTO ... SELECT ... without column names relies on position matching
        # which is guaranteed since we iterate source columns in order and build destination table same way.
        insert_query = f"""
        INSERT INTO {storage_db}.rep_{table_name}
        SELECT
            {", ".join(select_parts)}
        FROM {storage_db}.{table_name}
        """
        
        print(f"Executing INSERT for rep_{table_name}...")
        try:
            client.command(insert_query)
            print(f"Successfully inserted data into rep_{table_name}.")
        except Exception as e:
            print(f"Error inserting into rep_{table_name}: {e}")

if __name__ == "__main__":
    insert_data()
