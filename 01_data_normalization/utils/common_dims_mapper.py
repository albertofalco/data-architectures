"""
Mapeo de dimensiones comunes para columnas string/object compartidas entre tablas.

Este script identifica columnas que aparecen en multiples archivos CSV, Extrae
los valores unicos de cada columna, los ordena y genera un archivo mappings.json
con mapeos de valores a IDs enteros.

Usage:
    ./venv/bin/python 01_data_normalization/utils/common_dims_mapper.py
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

# Directorio donde se encuentra el script y directorio de datos crudos
SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent.parent / 'data' / 'raw'

# Archivos a excluir del analisis (no son datos de entrenamiento)
EXCLUDED_FILES = {'application_test.csv', 'HomeCredit_columns_description.csv', 'sample_submission.csv'}


def get_column_mapping(raw_dir):
    """
    Analiza los archivos CSV y genera un mapeo de columnas a archivos.

    Args:
        raw_dir: Directorio que contiene los archivos CSV

    Returns:
        tuple: (file_columns, column_to_files, file_dtypes)
        - file_columns: dict con nombres de archivos y sus columnas
        - column_to_files: defaultdict que mapea nombres de columnas a archivos
        - file_dtypes: dict con los tipos de datos de cada archivo
    """
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
    """
    Filtra columnas que aparecen en mas de un archivo y son de tipo string/object.

    Args:
        file_columns: dict con nombres de archivos y sus columnas
        column_to_files: mapeo de columnas a archivos
        file_dtypes: tipos de datos por archivo

    Returns:
        list: nombres de columnas que cumplen los criterios
    """
    common_string_cols = []

    for col, files in column_to_files.items():
        if len(files) < 2:
            continue

        dtype = file_dtypes[files[0]].get(col, '')
        if dtype in ['object', 'string']:
            common_string_cols.append(col)

    return common_string_cols


def get_consolidated_unique_values(raw_dir, column, files):
    """
    Extrae valores unicos de una columna desde multiples archivos y los consolida.

    Args:
        raw_dir: Directorio de datos crudos
        column: Nombre de la columna
        files: Lista de archivos que contienen la columna

    Returns:
        list: Valores unicos ordenados (alfabetico o por orden especial para dias)
    """
    all_values = set()

    for file_name in files:
        file_path = raw_dir / file_name
        df = pd.read_csv(file_path)

        if column in df.columns:
            values = df[column].dropna().astype(str).unique()
            all_values.update(values)

    # Orden especial para dias de la semana: lunes(1) a domingo(7)
    if column.upper() == 'WEEKDAY_APPR_PROCESS_START':
        day_order = {'MONDAY': 1, 'TUESDAY': 2, 'WEDNESDAY': 3, 'THURSDAY': 4, 'FRIDAY': 5, 'SATURDAY': 6, 'SUNDAY': 7}
        return sorted(all_values, key=lambda x: day_order.get(x, 999))

    return sorted(all_values)


def main():
    """
    Funcion principal que ejecuta el proceso de mapeo.

    1. Lee archivos CSV del directorio raw
    2. Identifica columnas comunes de tipo string/object
    3. Extrae y consolida valores unicos
    4. Genera mappings.json con valores mapeados a IDs
    """
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


if __name__ == '__main__':
    main()
