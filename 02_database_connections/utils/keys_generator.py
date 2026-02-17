import json
from pathlib import Path
import pandas as pd
import sys

# Define base paths relative to this script
# keys_generator.py is in 02_database_connections/utils/
# We need to go up 3 levels to reach root: utils -> 02_database_connections -> root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / 'data' / 'db_input'
OUTPUT_FILE = Path(__file__).resolve().parent / 'keys.json'

def get_csv_headers(file_path):
    """Read only the header (first row) of a CSV file."""
    try:
        # Read only 0 rows to get headers
        df = pd.read_csv(file_path, nrows=0)
        return df.columns.tolist()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def generate_keys():
    print(f"Scanning for CSV files in: {DATA_PATH}")
    
    # 1. Discovery: Find all CSV files recursively
    if not DATA_PATH.exists():
        print(f"Error: Data path does not exist: {DATA_PATH}")
        return []
        
    all_files = list(DATA_PATH.rglob('*.csv'))
    print(f"Found {len(all_files)} CSV files.")

    tables_metadata = []
    known_dim_pks = set()

    # 2. Pass 1: Identify Tables and Dimension PKs
    for f in all_files:
        table_name = f.stem
        is_dim = table_name.startswith('dim_')
        columns = get_csv_headers(f)
        
        pk = []
        
        # Rule for Dimensions: PK contains "ID"
        if is_dim:
            pk = [col for col in columns if "ID" in col]
            # Add to known set for FK matching later
            known_dim_pks.update(pk)
        
        # Rule for Main Tables: PK contains "SK" AND "ID"
        else:
            pk = [col for col in columns if "SK" in col and "ID" in col]

        tables_metadata.append({
            'name': table_name,
            'is_dim': is_dim,
            'columns': columns,
            'pk': pk,
            'fk': [] # To be filled in Pass 2
        })

    # 3. Pass 2: Identify FKs in Main Tables
    # FKs are columns that match known Dimension PKs
    
    final_output = []

    for table in tables_metadata:
        # FK logic: "La primary key creada va a ser la foreign key en las tablas de transacciones"
        # We assume Main Tables are the transaction tables.
        
        if not table['is_dim']:
            # Find columns that are in the set of known dimension PKs
            # Note: A column might be both a PK and an FK? 
            # Usually SK_ID_CURR is PK, CODE_GENDER_ID is FK.
            # We exclude the table's own PKs from being listed as FKs if they happen to overlap (unlikely with SK vs ID logic)
            
            fks = [col for col in table['columns'] if col in known_dim_pks and col not in table['pk']]
            table['fk'] = fks
        
        # Construct final object
        final_output.append({
            "table_name": table['name'],
            "pk": table['pk'],
            "fk": table['fk']
        })

    return final_output

if __name__ == "__main__":
    keys_data = generate_keys()
    
    # Export to JSON
    try:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(keys_data, f, indent=4)
        print(f"Successfully exported keys to: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error writing output file: {e}")
