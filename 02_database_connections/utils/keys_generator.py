"""Generate primary and foreign key metadata from normalized CSV files."""

# ==================== IMPORTS ====================

import json
from pathlib import Path
import pandas as pd
import sys

# ==================== CONFIGURATION ====================

# Resolve project paths relative to this utility.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / 'data' / 'db_input'
OUTPUT_FILE = Path(__file__).resolve().parent / 'keys.json'

# ==================== HELPER FUNCTIONS ====================

def get_csv_headers(file_path):
    """Return the column names from a CSV header."""
    try:
        # Read no data rows because only the header is needed.
        df = pd.read_csv(file_path, nrows=0)
        return df.columns.tolist()
    except Exception as e:
        print(f"Error leyendo {file_path}: {e}")
        return []

# ==================== MAIN FUNCTIONS ====================

def generate_keys():
    """Generate key metadata by scanning normalized CSV files."""
    print(f"Escaneando archivos CSV en: {DATA_PATH}")
    
    # Discover normalized CSV files recursively.
    if not DATA_PATH.exists():
        print(f"Error: DATA PATH no existe: {DATA_PATH}")
        return []
        
    all_files = list(DATA_PATH.rglob('*.csv'))
    print(f"Se encontraron {len(all_files)} archivos CSV.")

    tables_metadata = []
    known_dim_pks = set()

    # Identify tables and their candidate primary keys.
    for f in all_files:
        table_name = f.stem
        is_dim = table_name.startswith('dim_')
        columns = get_csv_headers(f)
        
        pk = []
        
        # Dimension primary keys contain ID.
        if is_dim:
            pk = [col for col in columns if "ID" in col]
            # Retain dimension keys for later foreign key matching.
            known_dim_pks.update(pk)
        
        # Transaction primary keys contain both SK and ID.
        else:
            pk = [col for col in columns if "SK" in col and "ID" in col]

        tables_metadata.append({
            'name': table_name,
            'is_dim': is_dim,
            'columns': columns,
            'pk': pk,
            'fk': []
        })

    # Match transaction columns against known dimension primary keys.
    
    final_output = []

    for table in tables_metadata:
        if not table['is_dim']:
            # Treat matching dimension keys as transaction foreign keys.
            fks = [col for col in table['columns'] if col in known_dim_pks and col not in table['pk']]
            table['fk'] = fks
        
        # Build the exported metadata record.
        final_output.append({
            "table_name": table['name'],
            "pk": table['pk'],
            "fk": table['fk']
        })

    return final_output

# ==================== EXECUTION ====================

if __name__ == "__main__":
    keys_data = generate_keys()
    
    # Export key metadata to JSON.
    try:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(keys_data, f, indent=4)
        print(f"Claves exportadas correctamente en: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error escribiendo archivo de salida: {e}")
