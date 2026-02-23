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
        # name, type, default_type, default_expression, comment, codec_expression, ttl_expression
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
    # Heuristic: matches dict_dim_{name_without_id}
    if col_name.upper().endswith("_ID"):
        base = col_name[:-3].lower()
        candidate = f"dict_dim_{base}"
        if candidate in dict_names:
            return candidate
        
        # Check for numeric suffix like _2 (e.g. ORGANIZATION_TYPE_2_ID -> dict_dim_organization_type)
        if len(base) > 2 and base[-2] == '_' and base[-1].isdigit():
            base_clean = base[:-2]
            candidate_clean = f"dict_dim_{base_clean}"
            if candidate_clean in dict_names:
                return candidate_clean
                
    return None

def create_dv_mv():
    config = load_config()
    staging_db = config["databases"]["staging_db"]
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
        print(f"Processing {table_name}...")
        
        src_cols = get_table_columns(client, storage_db, table_name)
        if not src_cols:
            print(f"Skipping {table_name} (source not found).")
            continue

        select_parts = []
        dest_col_defs = []
        order_col = None

        for col in src_cols:
            col_name = col['name']
            col_type = col['type']
            
            # Identify Order Column (PK)
            # For Option B, it's _DW_ID. For Option A, usually the first one (e.g. SK_ID_CURR)
            if order_col is None:
                order_col = col_name

            matching_dict = find_matching_dict(col_name, dict_names)
            
            if matching_dict:
                # Get dictionary schema
                dict_cols = get_dictionary_columns(client, storage_db, matching_dict)
                # Assume 2nd column is description (1st is ID)
                # Or find the one that is NOT matching the ID type/name? 
                # In 06_dw_config.md: dict_dim_status (STATUS_ID, STATUS)
                # The ID column in dict usually matches the suffix of col_name (STATUS_ID)
                # The description column is the other one.
                
                desc_col = None
                for dc in dict_cols:
                    if dc['name'] != col_name and not dc['name'].endswith('_ID'):
                        desc_col = dc
                        break
                # Fallback: just take the second column if available
                if not desc_col and len(dict_cols) > 1:
                    desc_col = dict_cols[1]
                
                if desc_col:
                    desc_name = desc_col['name']
                    desc_type = desc_col['type']
                    
                    target_alias = col_name[:-3]
                    
                    # Add dictGet
                    # dictGet('db.dict', 'attr', key)
                    select_parts.append(f"dictGet('{storage_db}.{matching_dict}', '{desc_name}', {col_name}) AS {target_alias}")
                    dest_col_defs.append(f"{target_alias} {desc_type}")
                else:
                    # Dictionary found but schema unclear, keep original
                    select_parts.append(col_name)
                    dest_col_defs.append(f"{col_name} {col_type}")
            else:
                select_parts.append(col_name)
                dest_col_defs.append(f"{col_name} {col_type}")

        # Construct Queries
        rep_table = f"rep_{table_name}"
        mv_table = f"mv_{table_name}"
        
        # Create Destination Table
        create_rep_sql = f"""
        CREATE TABLE IF NOT EXISTS {storage_db}.{rep_table}
        (
            {", ".join(dest_col_defs)}
        )
        ENGINE = MergeTree()
        ORDER BY {order_col}
        """
        
        try:
            client.command(create_rep_sql)
            print(f"Table {storage_db}.{rep_table} created.")
        except Exception as e:
            print(f"Error creating {rep_table}: {e}")
            continue

        # Create Materialized View
        # CREATE MATERIALIZED VIEW mv TO rep AS SELECT ... FROM storage
        create_mv_sql = f"""
        CREATE MATERIALIZED VIEW IF NOT EXISTS {storage_db}.{mv_table}
        TO {storage_db}.{rep_table}
        AS SELECT
            {", ".join(select_parts)}
        FROM {storage_db}.{table_name}
        """
        
        try:
            client.command(create_mv_sql)
            print(f"Materialized View {storage_db}.{mv_table} created.")
        except Exception as e:
            print(f"Error creating MV {mv_table}: {e}")

if __name__ == "__main__":
    create_dv_mv()
