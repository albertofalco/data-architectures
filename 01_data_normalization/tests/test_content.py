"""Validate normalized dataset content against the original raw CSV files."""

# ==================== IMPORTS ====================

import pandas as pd
import numpy as np
import os
from pathlib import Path
from pandasql import sqldf

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

EXCLUDE_COLUMNS = ['ORGANIZATION_TYPE', 'ORGANIZATION_TYPE_2']
TEST_ROW_LIMIT = 100000


# ==================== HELPER FUNCTIONS ====================

def load_dataframes(folder_path, table_name, use_nullable_int=True, nrows=None):
    """Load a normalized dataset and its local dimension tables."""
    full_path = folder_path / table_name
    
    if not full_path.exists():
        print(f"[ERROR] La carpeta {full_path} no existe.")
        return {}
    
    csv_files = [f for f in os.listdir(full_path) if f.endswith('.csv')]
    
    if not csv_files:
        print(f"[WARNING] No se encontraron archivos CSV en {full_path}")
        return {}
    
    dataframes = {}
    
    for file in csv_files:
        file_path = full_path / file
        try:
            # Apply the row limit only to the primary dataset.
            current_nrows = nrows if file == f"{table_name}.csv" else None
            df = pd.read_csv(file_path, keep_default_na=False, nrows=current_nrows)
            
            if use_nullable_int:
                for col in df.columns:
                    col_data = df[col]
                    if col_data.dtype == 'float64':
                        non_null = col_data[col_data != ''].dropna()
                        if len(non_null) > 0:
                            try:
                                int_check = pd.to_numeric(non_null, errors='coerce')
                                if int_check.notna().all():
                                    df[col] = df[col].replace('', np.nan).astype('Int64')
                            except:
                                pass
            
            key = file.replace('.csv', '')
            dataframes[key] = df
        except Exception as e:
            print(f"[ERROR] Error al leer '{file}': {e}")
    
    return dataframes


def get_matching_common_dims(main_df, common_dims):
    """Return common dimension tables referenced by a normalized dataset."""
    matching_dims = {}
    
    for dim_name, dim_df in common_dims.items():
        dim_id_col = dim_df.columns[0]
        if dim_id_col in main_df.columns:
            matching_dims[dim_name] = dim_df
    
    return matching_dims


def build_denormalized_query(dataframes, main_table, common_dims=None):
    """Build a query that joins a normalized dataset to its dimensions."""
    dim_tables = {k: v for k, v in dataframes.items() if k.startswith('dim_')}
    
    main_columns = list(dataframes[main_table].columns)
    
    select_columns = []
    for col in main_columns:
        if col.endswith('_ID'):
            col_base = col.replace('_ID', '')
            
            possible_dim_names = [
                f"dim_{col_base.lower()}",
                f"dim_{col_base}"
            ]
            
            dim_name = None
            for pdn in possible_dim_names:
                if pdn in dim_tables:
                    dim_name = pdn
                    break
            
            if dim_name:
                desc_col = dataframes[dim_name].columns[1]
                select_columns.append(f"{dim_name}.{desc_col} AS {col_base}")
            else:
                select_columns.append(f"{main_table}.{col}")
        else:
            select_columns.append(f"{main_table}.{col}")
    
    query = f"SELECT {', '.join(select_columns)} FROM {main_table}"
    
    for dim_name in dim_tables:
        id_col = dataframes[dim_name].columns[0]
        query += f" LEFT JOIN {dim_name} ON {main_table}.{id_col} = {dim_name}.{id_col}"
    
    return query


def denormalize_dataset(dataframes, main_table, common_dims=None):
    """Reconstruct a normalized dataset through its dimension joins."""
    if common_dims:
        dataframes.update(common_dims)
    
    query = build_denormalized_query(dataframes, main_table, common_dims)
    
    return sqldf(query, dataframes)


def validate_content(original_df, result_df, table_name):
    """Compare original and reconstructed dataset content."""
    print(f"\n{'='*70}")
    print(f"VALIDACIÓN DE CONTENIDO: {table_name}")
    print(f"{'='*70}")
    
    common_columns = [col for col in original_df.columns 
                      if col not in EXCLUDE_COLUMNS]
    
    errors = False
    differences_detail = []
    
    for col in common_columns:
        if col not in result_df.columns:
            continue
        
        if col.endswith('_ID'):
            continue
        
        try:
            orig_col = original_df[col].copy()
            res_col = result_df[col].copy()
            
            if orig_col.dtype != res_col.dtype:
                if pd.api.types.is_numeric_dtype(orig_col):
                    res_col = pd.to_numeric(res_col, errors='coerce')
            
            if not orig_col.equals(res_col):
                differences = (orig_col != res_col).sum()
                
                if pd.api.types.is_numeric_dtype(orig_col):
                    try:
                        max_diff = (abs(pd.to_numeric(orig_col, errors='coerce') - pd.to_numeric(res_col, errors='coerce'))).max()
                        if pd.notna(max_diff) and max_diff < 1e-5:
                            continue
                    except:
                        pass
                
                differences_detail.append({
                    'column': col,
                    'count': differences,
                    'percentage': (differences / len(original_df)) * 100
                })
        except Exception as e:
            differences_detail.append({
                'column': col,
                'count': -1,
                'percentage': 0
            })
    
    if differences_detail:
        print(f"[WARNING] Se encontraron diferencias en {len(differences_detail)} columnas:")
        for diff in differences_detail:
            if diff['count'] == -1:
                print(f"  - {diff['column']}: Error al comparar")
            else:
                print(f"  - {diff['column']}: {diff['count']} diferencias ({diff['percentage']:.2f}%)")
    else:
        print(f"[OK] Contenido validado")
    
    return True


# ==================== MAIN FUNCTIONS ====================

def run_tests(table_names=None):
    """Validate content for configured normalized datasets."""
    if table_names is None:
        table_names = LOOKUP_TABLES
    
    print("\n" + "="*70)
    print("CONTROL DE CONTENIDO - DATASETS NORMALIZADOS")
    print("="*70)

    print(f"\nCargando dimensiones comunes...")
    common_tables = load_dataframes(OUTPUT_DIR, 'common_dims')
    
    if not common_tables:
        raise Exception(f"No se pudieron cargar las tablas de dimensiones comunes desde {COMMON_DIM_DIR}")
    else:
        print(f"[OK] {len(common_tables)} dimensiones comunes cargadas")
    
    results = {}

    for table_name in table_names:
        print(f"\n\n{'#'*70}")
        print(f"# PROCESANDO: {table_name}")
        print(f"{'#'*70}")
        
        try:
            print(f"\nCargando datos normalizados (límite {TEST_ROW_LIMIT} registros)...")
            dataframes = load_dataframes(OUTPUT_DIR, table_name, nrows=TEST_ROW_LIMIT)
            
            if not dataframes:
                print(f"[ERROR] No se pudieron cargar los datos para {table_name}")
                results[table_name] = False
                continue
            
            print(f"[OK] {len(dataframes)} archivos cargados")
            
            main_df = dataframes[table_name]
            matching_common = get_matching_common_dims(main_df, common_tables)
            
            if matching_common:
                print(f"[OK] {len(matching_common)} dimensiones comunes detectadas para JOIN")
            
            print(f"Desnormalizando dataset...")
            result_df = denormalize_dataset(dataframes, table_name, matching_common)
            
            print(f"Cargando dataset original (límite {TEST_ROW_LIMIT} registros)...")
            original_path = RAW_DATA_DIR / f"{table_name}.csv"
            if not original_path.exists():
                print(f"[ERROR] Dataset original no encontrado: {original_path}")
                results[table_name] = False
                continue
            
            original_df = pd.read_csv(original_path, nrows=TEST_ROW_LIMIT)
            
            table_result = validate_content(original_df, result_df, table_name)
            results[table_name] = table_result
            
            print(f"\n{'='*70}")
            if table_result:
                print(f"[OK] VALIDACIONES COMPLETADAS EXITOSAMENTE: {table_name}")
            else:
                print(f"[WARNING] VALIDACIONES COMPLETADAS CON ALERTAS: {table_name}")
            print(f"{'='*70}")
            
        except Exception as e:
            print(f"\n[ERROR] Excepción al procesar {table_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results[table_name] = False
    
    print(f"\n\n{'='*70}")
    print("RESUMEN FINAL")
    print(f"{'='*70}")
    for table_name, passed in results.items():
        status = "[OK]" if passed else "[ERROR]"
        print(f"{status} {table_name}")
    
    all_passed = all(results.values())
    print(f"\n{'='*70}")
    if all_passed:
        print("[OK] TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    else:
        print("[WARNING] ALGUNAS PRUEBAS COMPLETADAS CON ALERTAS")
    print(f"{'='*70}\n")
    
    return results


# ==================== EXECUTION ====================

if __name__ == '__main__':
    run_tests()
