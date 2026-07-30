"""Create denormalized ClickHouse report tables and materialized views."""

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
    with open("03_dw_pipeline/src/config.yml", "r") as f:
        return yaml.safe_load(f)

def get_table_columns(client, database, table):
    """Return the names and types of the columns in a table."""
    query = f"DESCRIBE TABLE {database}.{table}"
    try:
        result = client.query(query)
        return [{'name': row[0], 'type': row[1]} for row in result.result_rows]
    except Exception as e:
        print(f"Error getting columns for {table}: {e}")
        return []

def get_dictionaries(client, database):
    """Return the dictionaries available in a database."""
    query = f"SHOW DICTIONARIES FROM {database}"
    result = client.query(query)
    return set([row[0] for row in result.result_rows])

def get_dictionary_columns(client, database, dict_name):
    """Return the column definitions for a dictionary."""
    query = f"DESCRIBE {database}.{dict_name}"
    result = client.query(query)
    return [{'name': row[0], 'type': row[1]} for row in result.result_rows]

def find_matching_dict(col_name, dict_names):
    """Find the dictionary associated with an identifier column."""
    # Match identifiers to dictionaries named dict_dim_<identifier>.
    if col_name.upper().endswith("_ID"):
        base = col_name[:-3].lower()
        candidate = f"dict_dim_{base}"
        if candidate in dict_names:
            return candidate
        
        # Ignore numeric suffixes such as ORGANIZATION_TYPE_2_ID.
        if len(base) > 2 and base[-2] == '_' and base[-1].isdigit():
            base_clean = base[:-2]
            candidate_clean = f"dict_dim_{base_clean}"
            if candidate_clean in dict_names:
                return candidate_clean
                
    return None

# ==================== MAIN FUNCTIONS ====================

def create_dv_mv():
    """Create report tables and views with dictionary descriptions."""
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
            
            # Use the first source column as the report table ordering key.
            if order_col is None:
                order_col = col_name

            matching_dict = find_matching_dict(col_name, dict_names)
            
            if matching_dict:
                # Locate the descriptive attribute in the dictionary schema.
                dict_cols = get_dictionary_columns(client, storage_db, matching_dict)
                
                desc_col = None
                for dc in dict_cols:
                    if dc['name'] != col_name and not dc['name'].endswith('_ID'):
                        desc_col = dc
                        break
                # Fall back to the dictionary's second column.
                if not desc_col and len(dict_cols) > 1:
                    desc_col = dict_cols[1]
                
                if desc_col:
                    desc_name = desc_col['name']
                    desc_type = desc_col['type']
                    
                    target_alias = col_name[:-3]
                    
                    select_parts.append(f"dictGet('{storage_db}.{matching_dict}', '{desc_name}', {col_name}) AS {target_alias}")
                    dest_col_defs.append(f"{target_alias} {desc_type}")
                else:
                    # Preserve the identifier when no description is available.
                    select_parts.append(col_name)
                    dest_col_defs.append(f"{col_name} {col_type}")
            else:
                select_parts.append(col_name)
                dest_col_defs.append(f"{col_name} {col_type}")

        # Build the report table and materialized view statements.
        rep_table = f"rep_{table_name}"
        mv_table = f"mv_{table_name}"
        
        # Create the destination report table.
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

        # Create the materialized view that populates the report table.
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

# ==================== EXECUTION ====================

if __name__ == "__main__":
    create_dv_mv()
