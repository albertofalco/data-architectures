"""
Script de normalización de base de datos.

Este script realiza operaciones de normalización de datos en múltiples datasets,
aplicando transformaciones como:
- Remapeo de valores usando mappings.json (dimensiones comunes)
- Atomización de valores (Primera Forma Normal)
- Creación de tablas de dimensiones para atributos categóricos
- Exportación de datos normalizados a CSV
"""

import pandas as pd
import numpy as np
import re
import os
import json
from pathlib import Path

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def convert_to_nullable_int(df):
    """Convierte columnas float64 a Int64 nullable donde es posible."""
    for col in df.columns:
        if df[col].dtype == 'float64':
            non_null = df[col].dropna()
            if len(non_null) > 0 and all(non_null == non_null.astype(int)):
                df[col] = df[col].astype('Int64')
    return df


def get_organization_type_2(org_type):
    """Extrae el número de tipo de organización."""
    if pd.isna(org_type):
        return 'Type 0'
    
    org_type_lower = str(org_type).lower()
    match_value = re.search(r'type\s*(\d+)', org_type_lower)
    if match_value:
        return f"Type {match_value.group(1)}"
    else:
        return "Type 0"


def clean_organization_type(org_type):
    """Limpia el tipo de organización eliminando el patrón 'type X'."""
    if pd.isna(org_type):
        return org_type
    
    org_type_str = str(org_type)
    cleaned_org_type = re.sub(
        r'[:-]?\s*type\s*\d+',
        '',
        org_type_str,
        flags=re.IGNORECASE
    ).strip()
    return cleaned_org_type if cleaned_org_type else org_type_str


def load_mappings(mappings_path):
    """
    Carga el archivo mappings.json y lo convierte en un diccionario.
    
    Parameters:
    -----------
    mappings_path : Path
        Ruta al archivo mappings.json
    
    Returns:
    --------
    dict : Diccionario con nombre de columna -> {valor: id}
    """
    with open(mappings_path, 'r') as f:
        mappings_list = json.load(f)
    
    mappings_dict = {}
    for item in mappings_list:
        for key, value in item.items():
            mappings_dict[key] = value
    
    return mappings_dict


def remap_with_mappings(csv_name, data_path, output_dir, mappings_dict):
    """
    Remapea valores usando mappings.json y crea tablas de dimensiones comunes.
    
    Parameters:
    -----------
    csv_name : str
        Nombre del archivo CSV a procesar
    data_path : Path
        Ruta a los datos de entrada
    output_dir : Path
        Ruta base para guardar los datos de salida
    mappings_dict : dict
        Diccionario de mapeos cargado desde mappings.json
    
    Returns:
    --------
    tuple : (df procesado, lista de columnas procesadas)
    """
    print(f"\n{'='*70}")
    print(f"Remapeando: {csv_name}")
    print(f"{'='*70}")
    
    df = pd.read_csv(data_path / csv_name)
    print(f"Dataset cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
    
    # 1NF - Atomización de ORGANIZATION_TYPE
    if 'ORGANIZATION_TYPE' in df.columns:
        print("\nAplicando Primera Forma Normal (1NF) - Atomización de ORGANIZATION_TYPE")
        df['ORGANIZATION_TYPE_2'] = df['ORGANIZATION_TYPE'].apply(get_organization_type_2)
        df['ORGANIZATION_TYPE'] = df['ORGANIZATION_TYPE'].apply(clean_organization_type)
    
    # Identificar columnas que están en mappings.json
    processed_columns = []
    
    for col_name, mapping in mappings_dict.items():
        col_name_upper = col_name.upper()
        if col_name_upper in df.columns:
            print(f"\nRemapeando columna: {col_name_upper}")
            
            unique_values = df[col_name_upper].dropna().unique()
            print(f"  - {col_name_upper}: {len(unique_values)} valores únicos en dataset")
            
            df[col_name_upper] = df[col_name_upper].map(mapping)
            df.rename(columns={col_name_upper: f'{col_name_upper}_ID'}, inplace=True)
            
            processed_columns.append(col_name_upper)
    
    # Guardar dataset principal
    ref_name = csv_name.replace('.csv', '')
    extract_dir = output_dir / ref_name
    
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    
    df = convert_to_nullable_int(df)
    df.to_csv(extract_dir / csv_name, index=False)
    print(f"\n✓ Dataset principal guardado: {extract_dir / csv_name}")
    
    return df, processed_columns


def normalize_dataset_standard(csv_name, data_path, output_dir, exclude_columns=None):
    """
    Normaliza un dataset para columnas categóricas NO incluidas en mappings.json.
    
    Parameters:
    -----------
    csv_name : str
        Nombre del archivo CSV a procesar
    data_path : Path
        Ruta a los datos de entrada
    output_dir : Path
        Ruta base para guardar los datos de salida
    exclude_columns : list
        Lista de columnas a excluir (ya procesadas con mappings.json)
    
    Returns:
    --------
    tuple : (df normalizado, diccionario de dimensiones)
    """
    if exclude_columns is None:
        exclude_columns = []
    
    print(f"\n{'='*70}")
    print(f"Normalizando: {csv_name}")
    print(f"{'='*70}")
    
    df = pd.read_csv(data_path / csv_name)
    print(f"Dataset cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
    
    # 1NF - Atomización de ORGANIZATION_TYPE (solo si no existe ya ORGANIZATION_TYPE_2)
    if 'ORGANIZATION_TYPE' in df.columns and 'ORGANIZATION_TYPE_2' not in df.columns:
        print("\nAplicando Primera Forma Normal (1NF) - Atomización de ORGANIZATION_TYPE")
        df['ORGANIZATION_TYPE_2'] = df['ORGANIZATION_TYPE'].apply(get_organization_type_2)
        df['ORGANIZATION_TYPE'] = df['ORGANIZATION_TYPE'].apply(clean_organization_type)
    
    # Crear tablas de dimensiones para columnas categóricas NO en exclude_columns
    print("\nCreando tablas de dimensiones...")
    
    categorical_columns = [
        col for col in df.columns 
        if df[col].dtype == 'object' and col not in exclude_columns
    ]
    
    dimension_tables = {}
    
    for col in categorical_columns:
        unique_values = df[col].dropna().unique()
        
        if len(unique_values) > 0:
            dim_df = pd.DataFrame({
                f'{col}_ID': range(1, len(unique_values) + 1),
                col: unique_values
            })
            dimension_tables[f'dim_{col.lower()}'] = dim_df
            
            mapping = dict(zip(dim_df[col], dim_df[f'{col}_ID']))
            df[col] = df[col].map(mapping)
            df.rename(columns={col: f'{col}_ID'}, inplace=True)
            
            print(f"  - {col}: {len(unique_values)} valores únicos")
    
    # Guardar dataset principal
    ref_name = csv_name.replace('.csv', '')
    extract_dir = output_dir / ref_name
    
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    
    df = convert_to_nullable_int(df)
    df.to_csv(extract_dir / csv_name, index=False)
    print(f"\n✓ Dataset principal guardado: {csv_name}")
    
    # Guardar tablas de dimensiones
    for name, dim_df in dimension_tables.items():
        file_name = f'{name}.csv'
        dim_df.to_csv(extract_dir / file_name, index=False)
        print(f"  ✓ Tabla de dimensiones guardada: {file_name}")
    
    print(f"\nDatos guardados en: {extract_dir}")
    
    return df, dimension_tables


def main():
    """Función principal que ejecuta la normalización de todos los datasets."""
    
    BASE_DIR = Path(__file__).resolve().parent
    data_path = BASE_DIR / ".." / ".." / "data" / "raw"
    output_dir = BASE_DIR / ".." / ".." / "data" / "db_input"
    mappings_path = BASE_DIR / ".." / "utils" / "mappings.json"
    
    # Cargar mappings.json
    mappings_dict = load_mappings(mappings_path)
    print(f"\nMappings cargados: {list(mappings_dict.keys())}")
    
    # Normalizar claves del mapping a mayúsculas para comparar con columnas de dataframes
    mapping_columns = {k.upper(): v for k, v in mappings_dict.items()}
    
    # Crear directorio common_dims y generar tablas de dimensiones desde mappings.json
    common_dims_dir = output_dir / 'common_dims'
    if not os.path.exists(common_dims_dir):
        os.makedirs(common_dims_dir)
    
    print("\n--- CREANDO DIMENSIONES COMUNES DESDE MAPPINGS.JSON ---")
    for col_name, mapping in mappings_dict.items():
        col_name_upper = col_name.upper()
        dim_data = []
        for value, id_val in sorted(mapping.items(), key=lambda x: x[1]):
            dim_data.append({f'{col_name_upper}_ID': id_val, col_name_upper: value})
        
        dim_df = pd.DataFrame(dim_data)
        dim_file_name = f'dim_{col_name.lower()}.csv'
        dim_df.to_csv(common_dims_dir / dim_file_name, index=False)
        print(f"  ✓ {dim_file_name}: {len(dim_data)} valores")
    
    # Todos los datasets a procesar
    all_datasets = [
        'application_train.csv',
        'application_test.csv',  # Incluido pero no procesado según indicación
        'bureau_balance.csv',
        'bureau.csv',
        'credit_card_balance.csv',
        'installments_payments.csv',
        'POS_CASH_balance.csv',
        'previous_application.csv'
    ]
    
    # Datasets excluidos explícitamente
    excluded_files = ['application_test.csv']
    
    # Determinar qué datasets tienen columnas del mappings.json
    datasets_with_mappings = []
    datasets_without_mappings = []
    mapping_columns_upper = list(mapping_columns.keys())
    
    for csv_name in all_datasets:
        if csv_name in excluded_files:
            continue
            
        try:
            df_temp = pd.read_csv(data_path / csv_name, nrows=0)
            cols_in_mappings = [col for col in mapping_columns_upper if col in df_temp.columns]
            
            if cols_in_mappings:
                datasets_with_mappings.append(csv_name)
            else:
                datasets_without_mappings.append(csv_name)
        except FileNotFoundError:
            print(f"⚠ Archivo no encontrado: {csv_name}")
    
    print("\n" + "="*70)
    print("NORMALIZACIÓN DE BASE DE DATOS - SCRIPT DE EJECUCIÓN")
    print("="*70)
    
    # ========================================================================
    # FASE 1: REMAPEO CON MAPPINGS.JSON
    # ========================================================================
    print("\n--- FASE 1: REMAPEO CON MAPPINGS.JSON ---")
    
    # Procesar datasets que tienen columnas del mappings.json
    for csv_name in datasets_with_mappings:
        try:
            remap_with_mappings(csv_name, data_path, output_dir, mappings_dict)
        except FileNotFoundError:
            print(f"⚠ Archivo no encontrado: {csv_name}")
        except Exception as e:
            print(f"✗ Error procesando {csv_name}: {str(e)}")
    
    # ========================================================================
    # FASE 2: NORMALIZACIÓN ESTÁNDAR
    # ========================================================================
    print("\n--- FASE 2: NORMALIZACIÓN ESTÁNDAR ---")
    
    # Datasets procesados en Fase 1 (ya tienen el remapeo de mappings.json)
    datasets_phase1 = ['application_train.csv', 'credit_card_balance.csv', 'POS_CASH_balance.csv', 'previous_application.csv']
    
    # Todos los datasets a normalizar
    all_datasets_to_normalize = [
        'application_train.csv',
        'bureau_balance.csv',
        'bureau.csv',
        'credit_card_balance.csv',
        'installments_payments.csv',
        'POS_CASH_balance.csv',
        'previous_application.csv'
    ]
    
    for csv_name in all_datasets_to_normalize:
        # Los datasets de Fase 1 ya fueron procesados, leer desde output_dir
        # Los demás leer desde data_path (original)
        if csv_name in datasets_phase1:
            input_path = output_dir / csv_name.replace('.csv', '')
        else:
            input_path = data_path
        
        try:
            normalize_dataset_standard(
                csv_name, 
                input_path, 
                output_dir, 
                exclude_columns=mapping_columns_upper
            )
        except FileNotFoundError:
            print(f"⚠ Archivo no encontrado: {csv_name}")
        except Exception as e:
            print(f"✗ Error procesando {csv_name}: {str(e)}")
    
    print("\n" + "="*70)
    print("NORMALIZACIÓN COMPLETADA")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
