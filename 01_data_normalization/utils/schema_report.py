"""Generate a schema report for columns shared across raw CSV files."""

# ==================== IMPORTS ====================

import pandas as pd
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
    """Collect columns, types, source files, and sample values from raw CSV files."""
    column_to_files = defaultdict(list)
    file_columns = {}
    file_dtypes = {}
    file_value_counts = {}

    csv_files = [f for f in raw_dir.glob('*.csv') if f.name not in EXCLUDED_FILES]

    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        columns = df.columns.tolist()
        file_columns[csv_file.name] = columns

        file_dtypes[csv_file.name] = df.dtypes.astype(str).to_dict()

        file_value_counts[csv_file.name] = {}
        for col in columns:
            unique_values = df[col].dropna().unique()[:10].tolist()
            file_value_counts[csv_file.name][col] = unique_values

        for col in columns:
            column_to_files[col].append(csv_file.name)

    return file_columns, column_to_files, file_dtypes, file_value_counts


def generate_report(file_columns, column_to_files, file_dtypes, file_value_counts):
    """Build a schema report for columns present in multiple files."""
    report_data = []

    for file_name, columns in file_columns.items():
        for col in columns:
            other_files = [f for f in column_to_files[col] if f != file_name]
            if other_files:
                report_data.append({
                    'Archivo': file_name,
                    'Columna': col,
                    'Tipo': file_dtypes[file_name].get(col, ''),
                    'Value Counts': file_value_counts[file_name].get(col, []),
                    'Tablas en las que se encuentra (*)': other_files
                })

    df_report = pd.DataFrame(report_data)
    return df_report


# ==================== MAIN FUNCTIONS ====================

def main():
    """Write the shared-column schema report to CSV."""
    raw_path = RAW_DIR.resolve()

    file_columns, column_to_files, file_dtypes, file_value_counts = get_column_mapping(raw_path)

    report_df = generate_report(file_columns, column_to_files, file_dtypes, file_value_counts)

    output_path = SCRIPT_DIR / 'schema_report.csv'
    report_df.to_csv(output_path, index=False)
    print(f"Reporte guardado en: {output_path}")


# ==================== EXECUTION ====================

if __name__ == '__main__':
    main()
