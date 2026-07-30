"""Validate normalized dataset rows and reconstructed column names."""

# ==================== IMPORTS ====================

import pandas as pd
import os
from pathlib import Path

# ==================== CONFIGURATION ====================

BASE_DIR = Path(__file__).resolve().parent.parent

LOOKUP_TABLES = [
    'application_train',
    'bureau',
    'bureau_balance',
    'credit_card_balance',
    'installments_payments',
    'POS_CASH_balance',
    'previous_application'
]

OUTPUT_DIR = BASE_DIR / '..' / 'data' / 'db_input'
RAW_DATA_DIR = BASE_DIR / '..' / 'data' / 'raw'
COMMON_DIM_DIR = OUTPUT_DIR / 'common_dims'

# ==================== HELPER FUNCTIONS ====================

def get_dimension_column_name(dim_name, table_dir):
    """Return the descriptive column name from a dimension CSV."""
    dim_filename = f"{dim_name}.csv"
    
    # Prefer a dataset-local dimension table.
    dim_path = table_dir / dim_filename
    if not dim_path.exists():
        # Fall back to the shared dimension directory.
        dim_path = COMMON_DIM_DIR / dim_filename
    
    if not dim_path.exists():
        return None
        
    try:
        # Read only the CSV header.
        df = pd.read_csv(dim_path, nrows=0)
        if len(df.columns) >= 2:
            return df.columns[1]
    except:
        # Treat unreadable dimension metadata as unavailable.
        pass
    return None

def rename_id_columns(df, table_name):
    """Rename dimension identifiers to their descriptive column names."""
    new_columns = {}
    table_dir = OUTPUT_DIR / table_name
    
    for col in df.columns:
        if col.endswith('_ID') and col != 'SK_ID_CURR' and col != 'SK_ID_BUREAU' and col != 'SK_ID_PREV': 
            # Preserve identifiers that do not reference lookup dimensions.
            
            col_base = col[:-3]
            dim_name = f"dim_{col_base.lower()}"
            
            real_col_name = get_dimension_column_name(dim_name, table_dir)
            
            if real_col_name:
                new_columns[col] = real_col_name
    
    if new_columns:
        print(f"  Renombrando columnas para validación: {new_columns}")
        
    return df.rename(columns=new_columns)

def validate_structure(original_df, input_df, table_name):
    """Compare original and normalized dataset row counts."""
    print(f"\n{'='*70}")
    print(f"VALIDACIÓN DE ESTRUCTURA: {table_name}")
    print(f"{'='*70}")
    
    print(f"Shape original:   {original_df.shape}")
    print(f"Shape input:      {input_df.shape}")
    
    if original_df.shape[0] != input_df.shape[0]:
        print(f"[ERROR] Número de filas diferente")
        return False
    
    # Column names are validated separately after dimension reconstruction.
    print(f"[OK] Estructura (filas) validada")
    return True

def validate_columns(original_df, input_df, table_name):
    """Compare columns after reconstructing dimension names."""
    print(f"\n{'='*70}")
    print(f"VALIDACIÓN DE COLUMNAS: {table_name}")
    print(f"{'='*70}")
    
    # Rename columns without modifying the input DataFrame.
    df_renamed = input_df.copy()
    df_renamed = rename_id_columns(df_renamed, table_name)
    
    errors = False
    
    # Report source columns missing from normalized data.
    missing_in_input = set(original_df.columns) - set(df_renamed.columns)
    if missing_in_input:
        print(f"[ERROR] Columnas faltantes en db_input (tras renombrado):")
        for col in missing_in_input:
            print(f"  - {col}")
        errors = True
        
    # Report normalized columns absent from the source.
    extra_in_input = set(df_renamed.columns) - set(original_df.columns)
    if extra_in_input:
        print(f"[WARNING] Columnas extra en db_input (tras renombrado):")
        for col in extra_in_input:
            print(f"  - {col}")
            
    if not errors:
        print(f"[OK] Columnas validadas")
    
    return not errors

# ==================== MAIN FUNCTIONS ====================

def run_tests():
    """Validate structure for all configured normalized datasets."""
    print("\n" + "="*70)
    print("CONTROL DE ESTRUCTURA - DATASETS NORMALIZADOS")
    print("="*70)
    
    results = {}
    
    for table_name in LOOKUP_TABLES:
        print(f"\n\n{'#'*70}")
        print(f"# PROCESANDO: {table_name}")
        print(f"{'#'*70}")
        
        try:
            # Load the original raw CSV.
            raw_path = RAW_DATA_DIR / f"{table_name}.csv"
            if not raw_path.exists():
                print(f"[ERROR] Archivo original no encontrado: {raw_path}")
                results[table_name] = False
                continue
                
            print(f"Cargando original: {raw_path.name}")
            original_df = pd.read_csv(raw_path)
            
            # Load the normalized primary dataset.
            input_path = OUTPUT_DIR / table_name / f"{table_name}.csv"
            if not input_path.exists():
                print(f"[ERROR] Archivo db_input no encontrado: {input_path}")
                results[table_name] = False
                continue
                
            print(f"Cargando input: {input_path.name}")
            input_df = pd.read_csv(input_path)
            
            # Validate rows and columns.
            struct_valid = validate_structure(original_df, input_df, table_name)
            col_valid = validate_columns(original_df, input_df, table_name)
            
            results[table_name] = struct_valid and col_valid
            
        except Exception as e:
            print(f"[ERROR] Excepción en {table_name}: {e}")
            results[table_name] = False

    print(f"\n\n{'='*70}")
    print("RESUMEN FINAL DE ESTRUCTURA")
    print(f"{'='*70}")
    for table_name, passed in results.items():
        status = "[OK]" if passed else "[ERROR]"
        print(f"{status} {table_name}")
    
    if all(results.values()):
        print("\n[OK] TODAS LAS PRUEBAS DE ESTRUCTURA COMPLETADAS EXITOSAMENTE")
    else:
        print("\n[WARNING] FALLARON ALGUNAS PRUEBAS DE ESTRUCTURA")

# ==================== EXECUTION ====================

if __name__ == '__main__':
    run_tests()
