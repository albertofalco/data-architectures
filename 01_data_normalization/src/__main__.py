"""Normalize configured raw CSV datasets and generate dimension tables."""

# ==================== IMPORTS ====================

import pandas as pd
import numpy as np
import re
import os
import json
from pathlib import Path

# ==================== HELPER FUNCTIONS ====================

def convert_to_nullable_int(df):
    """Convert integral floating-point columns to nullable integers."""
    for col in df.columns:
        if df[col].dtype == 'float64':
            non_null = df[col].dropna()
            if len(non_null) > 0 and all(non_null == non_null.astype(int)):
                df[col] = df[col].astype('Int64')
    return df


def get_organization_type_2(org_type):
    """Extract the numbered organization type label from a value."""
    if pd.isna(org_type):
        return 'Type 0'
    
    org_type_lower = str(org_type).lower()
    match_value = re.search(r'type\s*(\d+)', org_type_lower)
    if match_value:
        return f"Type {match_value.group(1)}"
    else:
        return "Type 0"


def clean_organization_type(org_type):
    """Remove the numbered type suffix from an organization value."""
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
    """Load column value mappings from a JSON file."""
    with open(mappings_path, 'r') as f:
        mappings_list = json.load(f)
    
    mappings_dict = {}
    for item in mappings_list:
        for key, value in item.items():
            mappings_dict[key] = value
    
    return mappings_dict


def remap_with_mappings(csv_name, data_path, output_dir, mappings_dict):
    """Apply common dimension mappings to one raw CSV dataset."""
    print(f"\n{'='*70}")
    print(f"Remapeando: {csv_name}")
    print(f"{'='*70}")
    
    df = pd.read_csv(data_path / csv_name)
    print(f"Dataset cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
    
    # Split ORGANIZATION_TYPE into atomic 1NF values.
    if 'ORGANIZATION_TYPE' in df.columns:
        print("\nAplicando Primera Forma Normal (1NF) - Atomización de ORGANIZATION_TYPE")
        df['ORGANIZATION_TYPE_2'] = df['ORGANIZATION_TYPE'].apply(get_organization_type_2)
        df['ORGANIZATION_TYPE'] = df['ORGANIZATION_TYPE'].apply(clean_organization_type)
    
    # Identify columns configured in mappings.json.
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
    
    # Write the normalized primary dataset.
    ref_name = csv_name.replace('.csv', '')
    extract_dir = output_dir / ref_name
    
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    
    df = convert_to_nullable_int(df)
    df.to_csv(extract_dir / csv_name, index=False)
    print(f"\n✓ Dataset principal guardado: {extract_dir / csv_name}")
    
    return df, processed_columns


def normalize_dataset_standard(csv_name, data_path, output_dir, exclude_columns=None):
    """Normalize unmapped categorical columns into dimension tables."""
    if exclude_columns is None:
        exclude_columns = []
    
    print(f"\n{'='*70}")
    print(f"Normalizando: {csv_name}")
    print(f"{'='*70}")
    
    df = pd.read_csv(data_path / csv_name)
    print(f"Dataset cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
    
    # Split ORGANIZATION_TYPE when it has not already been processed.
    if 'ORGANIZATION_TYPE' in df.columns and 'ORGANIZATION_TYPE_2' not in df.columns:
        print("\nAplicando Primera Forma Normal (1NF) - Atomización de ORGANIZATION_TYPE")
        df['ORGANIZATION_TYPE_2'] = df['ORGANIZATION_TYPE'].apply(get_organization_type_2)
        df['ORGANIZATION_TYPE'] = df['ORGANIZATION_TYPE'].apply(clean_organization_type)
    
    # Create dimension tables for unmapped categorical columns.
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
    
    # Write the normalized primary dataset.
    ref_name = csv_name.replace('.csv', '')
    extract_dir = output_dir / ref_name
    
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    
    df = convert_to_nullable_int(df)
    df.to_csv(extract_dir / csv_name, index=False)
    print(f"\n✓ Dataset principal guardado: {csv_name}")
    
    # Write local dimension tables.
    for name, dim_df in dimension_tables.items():
        file_name = f'{name}.csv'
        dim_df.to_csv(extract_dir / file_name, index=False)
        print(f"  ✓ Tabla de dimensiones guardada: {file_name}")
    
    print(f"\nDatos guardados en: {extract_dir}")
    
    return df, dimension_tables


# ==================== MAIN FUNCTIONS ====================

def main():
    """Normalize all configured raw datasets."""
    
    BASE_DIR = Path(__file__).resolve().parent
    data_path = BASE_DIR / ".." / ".." / "data" / "raw"
    output_dir = BASE_DIR / ".." / ".." / "data" / "db_input"
    mappings_path = BASE_DIR / ".." / "utils" / "mappings.json"
    
    # Load shared dimension mappings.
    mappings_dict = load_mappings(mappings_path)
    print(f"\nMappings cargados: {list(mappings_dict.keys())}")
    
    # Normalize mapping keys for case-sensitive column matching.
    mapping_columns = {k.upper(): v for k, v in mappings_dict.items()}
    
    # Generate shared dimension tables from configured mappings.
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
    
    # Define candidate raw datasets.
    all_datasets = [
        'application_train.csv',
        'application_test.csv',
        'bureau_balance.csv',
        'bureau.csv',
        'credit_card_balance.csv',
        'installments_payments.csv',
        'POS_CASH_balance.csv',
        'previous_application.csv'
    ]
    
    # Exclude datasets that must not be normalized.
    excluded_files = ['application_test.csv']
    
    # Group datasets by whether they use shared mappings.
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
    
    print("\n--- FASE 1: REMAPEO CON MAPPINGS.JSON ---")
    
    # Apply shared mappings in the first phase.
    for csv_name in datasets_with_mappings:
        try:
            remap_with_mappings(csv_name, data_path, output_dir, mappings_dict)
        except FileNotFoundError:
            print(f"⚠ Archivo no encontrado: {csv_name}")
        except Exception as e:
            print(f"✗ Error procesando {csv_name}: {str(e)}")
    
    print("\n--- FASE 2: NORMALIZACIÓN ESTÁNDAR ---")
    
    # Track datasets already written during the mapping phase.
    datasets_phase1 = ['application_train.csv', 'credit_card_balance.csv', 'POS_CASH_balance.csv', 'previous_application.csv']
    
    # Define datasets for standard categorical normalization.
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
        # Read mapped datasets from output and all others from raw input.
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


# ==================== EXECUTION ====================

if __name__ == '__main__':
    main()
