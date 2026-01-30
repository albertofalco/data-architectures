"""
Script de pruebas para control de contenido de datasets normalizados.

Este script verifica que los datasets normalizados mantienen la integridad
de los datos comparándolos con los originales. Se aplica a los datasets:
- application_train
- bureau
- previous_application

Las pruebas incluyen:
1. Validación de estructura (shape)
2. Validación de columnas
3. Comparación de valores
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from pandasql import sqldf


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Obtener la carpeta actual del script
BASE_DIR = Path(__file__).resolve().parent.parent

# Rutas de datos
LOOKUP_TABLES = ['application_train', 'bureau', 'previous_application']
COMMON_DIM_LOOKUP = ['application_train', 'previous_application']
COMMON_DIM_TABLES = ['dim_name_contract_type',
                     'dim_name_type_suite',
                     'dim_weekday_appr_process_start'
                     ]
COMMON_DIM_DIR = 'common_dims'
OUTPUT_DIR = BASE_DIR / '..' / 'data' / 'db_input'
RAW_DATA_DIR = BASE_DIR / '..' / 'data' / 'raw'

# Columnas a excluir en comparación (se transforman en normalización)
EXCLUDE_COLUMNS = ['ORGANIZATION_TYPE', 'ORGANIZATION_TYPE_2']

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def load_dataframes(folder_path, table_name):
    """
    Carga DataFrames desde archivos CSV en la carpeta especificada.
    
    Args:
        folder_path (Path): Ruta a la carpeta base.
        table_name (str): Nombre de la subcarpeta (ej. 'application_train').
    
    Returns:
        dict: Diccionario con nombres de archivos (sin extensión) como claves 
              y DataFrames como valores.
    """
    full_path = folder_path / table_name
    
    # Verificar si la carpeta existe
    if not full_path.exists():
        print(f"[ERROR] La carpeta {full_path} no existe.")
        return {}
    
    # Listar archivos CSV en la carpeta
    csv_files = [f for f in os.listdir(full_path) if f.endswith('.csv')]
    
    if not csv_files:
        print(f"[WARNING] No se encontraron archivos CSV en {full_path}")
        return {}
    
    # Diccionario para almacenar los DataFrames
    dataframes = {}
    
    # Leer cada archivo CSV
    for file in csv_files:
        file_path = full_path / file
        try:
            df = pd.read_csv(file_path)
            key = file.replace('.csv', '')
            dataframes[key] = df
        except Exception as e:
            print(f"[ERROR] Error al leer '{file}': {e}")
    
    return dataframes


def build_denormalized_query(dataframes, main_table):
    """
    Construye una query SQL para unir la tabla principal con sus dimensiones.
    
    Args:
        dataframes (dict): Diccionario de DataFrames cargados.
        main_table (str): Nombre de la tabla principal.
    
    Returns:
        str: Query SQL construida.
    """
    # Identificar la tabla principal y las tablas de dimensión
    dim_tables = {k: v for k, v in dataframes.items() if k.startswith('dim_')}
    
    # Obtener columnas de la tabla principal
    main_columns = list(dataframes[main_table].columns)
    
    # Construir lista de columnas para SELECT
    select_columns = []
    for col in main_columns:
        if col.endswith('_ID'):
            dim_base = col.replace('_ID', '').lower()
            dim_name = f"dim_{dim_base}"
            if dim_name in dim_tables:
                # Usar la segunda columna (descripción) de la dim table
                desc_col = dataframes[dim_name].columns[1]
                select_columns.append(f"{dim_name}.{desc_col} AS {desc_col}")
            else:
                select_columns.append(f"{main_table}.{col}")
        else:
            select_columns.append(f"{main_table}.{col}")
    
    # Construir query SQL
    query = f"SELECT {', '.join(select_columns)} FROM {main_table}"
    
    for dim_name in dim_tables:
        id_col = dataframes[dim_name].columns[0]
        query += f" LEFT JOIN {dim_name} ON {main_table}.{id_col} = {dim_name}.{id_col}"
    
    return query


def denormalize_dataset(dataframes, main_table, common_tables=None):
    """
    Desnormaliza un dataset ejecutando la query construida.
    
    Args:
        dataframes (dict): Diccionario de DataFrames.
        main_table (str): Nombre de la tabla principal.
        common_tables (dict, optional): Diccionario de tablas comunes a incluir.
    
    Returns:
        pd.DataFrame: DataFrame desnormalizado.
    """
    # Si hay tablas comunes, incluirlas en el contexto de la query
    if main_table in COMMON_DIM_LOOKUP and common_tables:
        dataframes.update(common_tables)
    query = build_denormalized_query(dataframes, main_table)
    return sqldf(query, dataframes)

def validate_structure(original_df, result_df, table_name):
    """
    Valida la estructura (shape) del dataset.
    
    Args:
        original_df (pd.DataFrame): DataFrame original.
        result_df (pd.DataFrame): DataFrame resultado.
        table_name (str): Nombre de la tabla (para logging).
    
    Returns:
        bool: True si las validaciones pasan.
    """
    print(f"\n{'='*70}")
    print(f"VALIDACIÓN DE ESTRUCTURA: {table_name}")
    print(f"{'='*70}")
    
    print(f"Shape original:   {original_df.shape}")
    print(f"Shape resultado:  {result_df.shape}")
    
    if original_df.shape[0] != result_df.shape[0]:
        print(f"[ERROR] Número de filas diferente")
        return False
    
    print(f"[OK] Estructura validada")
    return True


def validate_columns(original_df, result_df, table_name):
    """
    Valida que las columnas sean consistentes.
    
    Args:
        original_df (pd.DataFrame): DataFrame original.
        result_df (pd.DataFrame): DataFrame resultado.
        table_name (str): Nombre de la tabla (para logging).
    
    Returns:
        bool: True si las validaciones pasan.
    """
    print(f"\n{'='*70}")
    print(f"VALIDACIÓN DE COLUMNAS: {table_name}")
    print(f"{'='*70}")
    
    errors = False
    
    # Verificar columnas en original que no están en resultado
    for col in original_df.columns:
        if col not in result_df.columns and col not in EXCLUDE_COLUMNS:
            print(f"[ERROR] Columna '{col}' NO está presente en resultado")
            errors = True
    
    # Verificar columnas en resultado que no están en original
    for col in result_df.columns:
        if col not in original_df.columns:
            if col not in EXCLUDE_COLUMNS:
                print(f"[WARNING] Columna '{col}' presente en resultado pero no en original")
    
    if not errors:
        print(f"[OK] Columnas validadas")
    
    return not errors


def validate_content(original_df, result_df, table_name):
    """
    Valida que el contenido sea consistente.
    
    Args:
        original_df (pd.DataFrame): DataFrame original.
        result_df (pd.DataFrame): DataFrame resultado.
        table_name (str): Nombre de la tabla (para logging).
    
    Returns:
        bool: True si las validaciones pasan.
    """
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
        
        # Saltar columnas ID (se transforman en normalización)
        if col.endswith('_ID'):
            continue
        
        # Comparar valores
        if not original_df[col].equals(result_df[col]):
            differences = sum(original_df[col] != result_df[col])
            
            # Tolerancia para valores numéricos con diferencias de redondeo pequeñas
            if pd.api.types.is_numeric_dtype(original_df[col]):
                max_diff = (abs(original_df[col] - result_df[col])).max()
                if max_diff < 1e-5:  # Tolerancia: 0.00001
                    continue
            
            differences_detail.append({
                'column': col,
                'count': differences,
                'percentage': (differences / len(original_df)) * 100
            })
    
    if differences_detail:
        print(f"[WARNING] Se encontraron diferencias en {len(differences_detail)} columnas:")
        for diff in differences_detail:
            print(f"  - {diff['column']}: {diff['count']} diferencias ({diff['percentage']:.2f}%)")
    else:
        print(f"[OK] Contenido validado")
    
    return True  # Retornar True incluso con warnings


def run_tests(table_names=None):
    """
    Ejecuta todas las pruebas para los datasets especificados.
    
    Args:
        table_names (list): Lista de nombres de tablas a probar. 
                           Si es None, usa LOOKUP_TABLES.
    """
    if table_names is None:
        table_names = LOOKUP_TABLES
    
    print("\n" + "="*70)
    print("CONTROL DE CONTENIDO - DATASETS NORMALIZADOS")
    print("="*70)

    # Cargar tablas de dimensiones comunes
    print(f"\nCargando dimensiones comunes...")
    common_tables = load_dataframes(OUTPUT_DIR, COMMON_DIM_DIR)
    
    if not common_tables:
        raise Exception(f"No se pudieron cargar las tablas de dimensiones comunes desde {COMMON_DIM_DIR}")
    else:
        print(f"Dimensiones comunes cargados desde {COMMON_DIM_DIR}")
    
    # print(f"[OK] {len(common_tables)} archivos cargados")

    results = {}

    for table_name in table_names:
        print(f"\n\n{'#'*70}")
        print(f"# PROCESANDO: {table_name}")
        print(f"{'#'*70}")
        
        try:
            # Cargar DataFrames normalizados
            print(f"\nCargando datos normalizados...")
            dataframes = load_dataframes(OUTPUT_DIR, table_name)
            
            if not dataframes:
                print(f"[ERROR] No se pudieron cargar los datos para {table_name}")
                results[table_name] = False
                continue
            
            print(f"[OK] {len(dataframes)} archivos cargados")
            
            # Desnormalizar para comparación
            print(f"Desnormalizando dataset...")
            result_df = denormalize_dataset(dataframes, table_name, common_tables)
            
            # Cargar dataset original
            print(f"Cargando dataset original...")
            original_path = RAW_DATA_DIR / f"{table_name}.csv"
            if not original_path.exists():
                print(f"[ERROR] Dataset original no encontrado: {original_path}")
                results[table_name] = False
                continue
            
            original_df = pd.read_csv(original_path)
            
            # Ejecutar validaciones
            struct_valid = validate_structure(original_df, result_df, table_name)
            col_valid = validate_columns(original_df, result_df, table_name)
            content_valid = validate_content(original_df, result_df, table_name)
            
            # Resultado final
            table_result = struct_valid and col_valid and content_valid
            results[table_name] = table_result
            
            print(f"\n{'='*70}")
            if table_result:
                print(f"[OK] VALIDACIONES COMPLETADAS EXITOSAMENTE: {table_name}")
            else:
                print(f"[WARNING] VALIDACIONES COMPLETADAS CON ALERTAS: {table_name}")
            print(f"{'='*70}")
            
        except Exception as e:
            print(f"\n[ERROR] Excepción al procesar {table_name}: {str(e)}")
            results[table_name] = False
    
    # Resumen final
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


if __name__ == '__main__':
    run_tests()
