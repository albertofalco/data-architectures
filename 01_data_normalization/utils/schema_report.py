"""
Reporte de esquema de datos.

Este script analiza archivos CSV y genera un reporte que muestra:
- Columnas presentes en multiples archivos
- Tipo de datos de cada columna
- Valores de ejemplo (hasta 10 por columna)
- Lista de archivos donde aparece cada columna

Usage:
    ./venv/bin/python 01_data_normalization/utils/schema_report.py
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict

# Directorio donde se encuentra el script y directorio de datos crudos
SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent.parent / 'data' / 'raw'

# Archivos a excluir del reporte (no son datos de entrenamiento)
EXCLUDED_FILES = {'application_test.csv', 'HomeCredit_columns_description.csv', 'sample_submission.csv'}


def get_column_mapping(raw_dir):
    """
    Analiza los archivos CSV y genera mapeos de columnas a archivos y tipos de datos.

    Args:
        raw_dir: Directorio que contiene los archivos CSV

    Returns:
        tuple: (file_columns, column_to_files, file_dtypes, file_value_counts)
        - file_columns: dict con nombres de archivos y sus columnas
        - column_to_files: defaultdict que mapea nombres de columnas a archivos
        - file_dtypes: dict con los tipos de datos de cada archivo
        - file_value_counts: dict con valores de ejemplo por columna
    """
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
    """
    Genera un DataFrame con el reporte de esquema.

    El reporte incluye solo columnas que aparecen en mas de un archivo.

    Args:
        file_columns: dict con nombres de archivos y sus columnas
        column_to_files: mapeo de columnas a archivos
        file_dtypes: tipos de datos por archivo
        file_value_counts: valores de ejemplo por columna

    Returns:
        DataFrame con el reporte generado
    """
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


def main():
    """
    Funcion principal que genera el reporte de esquema.

    1. Lee archivos CSV del directorio raw
    2. Analiza columnas, tipos y valores
    3. Genera reporte CSV con columnas comunes
    """
    raw_path = RAW_DIR.resolve()

    file_columns, column_to_files, file_dtypes, file_value_counts = get_column_mapping(raw_path)

    report_df = generate_report(file_columns, column_to_files, file_dtypes, file_value_counts)

    output_path = SCRIPT_DIR / 'schema_report.csv'
    report_df.to_csv(output_path, index=False)
    print(f"Reporte guardado en: {output_path}")


if __name__ == '__main__':
    main()
