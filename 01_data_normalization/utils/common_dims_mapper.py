"""Generate shared dimension value mappings from raw CSV files."""

# ==================== IMPORTS ====================

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

# ==================== CONFIGURATION ====================

# Project and raw data paths.
SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent.parent / 'data' / 'raw'

# Exclude files that are not training datasets.
EXCLUDED_FILES = {'application_test.csv', 'HomeCredit_columns_description.csv', 'sample_submission.csv'}


# ==================== HELPER FUNCTIONS ====================

def get_column_mapping(raw_dir):
    """Collect columns, source files, and inferred types from raw CSV files."""
    column_to_files = defaultdict(list)
    file_columns = {}
    file_dtypes = {}

    all_files = list(raw_dir.iterdir())
    csv_files = [f for f in all_files if f.name.endswith('.csv') and f.name not in EXCLUDED_FILES]

    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        columns = df.columns.tolist()
        file_columns[csv_file.name] = columns
        file_dtypes[csv_file.name] = df.dtypes.astype(str).to_dict()

        for col in columns:
            column_to_files[col].append(csv_file.name)

    return file_columns, column_to_files, file_dtypes


def get_common_string_columns(file_columns, column_to_files, file_dtypes):
    """Return string columns shared by multiple raw CSV files."""
    common_string_cols = []

    for col, files in column_to_files.items():
        if len(files) < 2:
            continue

        dtype = file_dtypes[files[0]].get(col, '')
        if dtype in ['object', 'string']:
            common_string_cols.append(col)

    return common_string_cols


def get_consolidated_unique_values(raw_dir, column, files):
    """Return sorted unique values for a column across raw CSV files."""
    all_values = set()

    for file_name in files:
        file_path = raw_dir / file_name
        df = pd.read_csv(file_path)

        if column in df.columns:
            values = df[column].dropna().astype(str).unique()
            all_values.update(values)

    # Preserve weekday order from Monday through Sunday.
    if column.upper() == 'WEEKDAY_APPR_PROCESS_START':
        day_order = {'MONDAY': 1, 'TUESDAY': 2, 'WEDNESDAY': 3, 'THURSDAY': 4, 'FRIDAY': 5, 'SATURDAY': 6, 'SUNDAY': 7}
        return sorted(all_values, key=lambda x: day_order.get(x, 999))

    return sorted(all_values)


# ==================== MAIN FUNCTIONS ====================

def main():
    """Generate shared dimension mappings from raw CSV values."""
    raw_path = RAW_DIR.resolve()

    file_columns, column_to_files, file_dtypes = get_column_mapping(raw_path)
    common_cols = get_common_string_columns(file_columns, column_to_files, file_dtypes)

    mappings = []
    for col in common_cols:
        files = column_to_files[col]
        unique_values = get_consolidated_unique_values(raw_path, col, files)

        value_to_id = {val: idx + 1 for idx, val in enumerate(unique_values)}

        mappings.append({col.lower(): value_to_id})

    output_path = SCRIPT_DIR / 'mappings.json'
    with open(output_path, 'w') as f:
        json.dump(mappings, f, indent=2)

    print(f"Mapeos guardados en: {output_path}")


# ==================== EXECUTION ====================

if __name__ == '__main__':
    main()
