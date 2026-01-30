"""
Script de normalización de base de datos.

Este script realiza operaciones de normalización de datos en múltiples datasets,
aplicando transformaciones como:
- Atomización de valores (Primera Forma Normal)
- Creación de tablas de dimensiones (mejoras de diseño)
- Exportación de datos normalizados a CSV
- Resolución de solapamientos de dimensiones entre application_train y previous_application
"""

import pandas as pd
import numpy as np
import re
import os
from pathlib import Path

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

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


def normalize_dataset(csv_name, data_path, output_dir, skip_dimension_export=False):
    """
    Normaliza un dataset específico.
    
    Realiza las siguientes operaciones:
    1. Lee el CSV
    2. Aplica transformaciones de 1NF (si aplica)
    3. Crea tablas de dimensiones para atributos categóricos
    4. Guarda el dataset normalizado y las dimensiones (si aplica)
    
    Parameters:
    -----------
    csv_name : str
        Nombre del archivo CSV a procesar
    data_path : str
        Ruta a los datos de entrada
    output_dir : str
        Ruta base para guardar los datos de salida
    skip_dimension_export : bool
        Si True, no exporta las dimensiones (usadas para application_train y previous_application
        que requieren correcciones de overlap)
    
    Returns:
    --------
    tuple : (df normalizado, diccionario de dimensiones)
    """
    
    print(f"\n{'='*70}")
    print(f"Procesando: {csv_name}")
    print(f"{'='*70}")
    
    # ========================================================================
    # 1. LECTURA DEL DATASET
    # ========================================================================
    df = pd.read_csv(data_path / csv_name)
    print(f"Dataset cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
    
    # ========================================================================
    # 2. PRIMERA FORMA NORMAL - Atomización de ORGANIZATION_TYPE
    # ========================================================================
    if 'ORGANIZATION_TYPE' in df.columns:
        print("\nAplicando Primera Forma Normal (1NF) - Atomización de ORGANIZATION_TYPE")
        df['ORGANIZATION_TYPE_2'] = df['ORGANIZATION_TYPE'].apply(get_organization_type_2)
        df['ORGANIZATION_TYPE'] = df['ORGANIZATION_TYPE'].apply(clean_organization_type)
    
    # ========================================================================
    # 3. MEJORAS DE DISEÑO - Creación de Tablas de Dimensiones
    # ========================================================================
    print("\nCreando tablas de dimensiones...")
    
    # Identificar columnas categóricas
    categorical_columns = [col for col in df.columns if df[col].dtype == 'object']
    dimension_tables = {}
    
    for col in categorical_columns:
        # Extraer valores únicos no NaN para la tabla de dimensión
        unique_values = df[col].dropna().unique()
        
        if len(unique_values) > 0:
            # Crear tabla de dimensión
            dim_df = pd.DataFrame({
                f'{col}_ID': range(1, len(unique_values) + 1),
                col: unique_values
            })
            dimension_tables[f'dim_{col.lower()}'] = dim_df
            
            # Crear mapeo y reemplazar valores con IDs
            mapping = dict(zip(dim_df[col], dim_df[f'{col}_ID']))
            df[col] = df[col].map(mapping)
            df.rename(columns={col: f'{col}_ID'}, inplace=True)
            
            print(f"  - {col}: {len(unique_values)} valores únicos")
    
    # ========================================================================
    # 4. EXPORTACIÓN DE DATOS NORMALIZADOS (si no se deben saltear)
    # ========================================================================
    print("\nExportando datos normalizados...")
    
    # Crear directorio de salida
    ref_name = csv_name.replace('.csv', '')
    extract_dir = output_dir / ref_name# output_dir  ref_name + '/'
    print(extract_dir)
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    
    # Guardar dataset principal
    df.to_csv(extract_dir / csv_name, index=False)
    print(f"  ✓ Dataset principal guardado: {csv_name}")
    
    # Guardar tablas de dimensiones
    for name, dim_df in dimension_tables.items():
        file_name = f'{name}.csv'
        dim_df.to_csv(extract_dir / file_name, index=False)
        print(f"  ✓ Tabla de dimensiones guardada: {file_name}")
    
    print(f"\nDatos guardados en: {extract_dir}")
    
    return df, dimension_tables


def apply_overlap_corrections(output_dir):
    """
    Aplica correcciones de solapamiento de dimensiones entre
    application_train y previous_application.
    
    Identifica 3 tablas de dimensiones compartidas y ajusta los IDs
    en ambos datasets para que coincidan con las dimensiones de referencia.
    """
    
    print("\n" + "="*70)
    print("EJECUCIÓN DE CORRECCIONES DE OVERLAP")
    print("="*70)
    
    # ========================================================================
    # 1. CREAR DIMENSIONES DE REFERENCIA
    # ========================================================================
    print("\n1. Creando tablas de dimensiones de referencia...")
    
    # dim_name_contract_type: usar como referencia previous_application
    dim_name_contract_type_ref = pd.read_csv(
        output_dir / 'previous_application' / 'dim_name_contract_type.csv'
    )
    print("  ✓ dim_name_contract_type (referencia: previous_application)")
    
    # dim_weekday_appr_process_start: crear versión estandarizada
    dim_weekday_appr_process_start_data = [
        {'WEEKDAY_APPR_PROCESS_START_ID': 1, 'WEEKDAY_APPR_PROCESS_START': 'MONDAY'},
        {'WEEKDAY_APPR_PROCESS_START_ID': 2, 'WEEKDAY_APPR_PROCESS_START': 'TUESDAY'},
        {'WEEKDAY_APPR_PROCESS_START_ID': 3, 'WEEKDAY_APPR_PROCESS_START': 'WEDNESDAY'},
        {'WEEKDAY_APPR_PROCESS_START_ID': 4, 'WEEKDAY_APPR_PROCESS_START': 'THURSDAY'},
        {'WEEKDAY_APPR_PROCESS_START_ID': 5, 'WEEKDAY_APPR_PROCESS_START': 'FRIDAY'},
        {'WEEKDAY_APPR_PROCESS_START_ID': 6, 'WEEKDAY_APPR_PROCESS_START': 'SATURDAY'},
        {'WEEKDAY_APPR_PROCESS_START_ID': 7, 'WEEKDAY_APPR_PROCESS_START': 'SUNDAY'}
    ]
    dim_weekday_appr_process_start_ref = pd.DataFrame(
        dim_weekday_appr_process_start_data
    )
    print("  ✓ dim_weekday_appr_process_start (versión estandarizada)")
    
    # dim_name_type_suite: usar como referencia previous_application
    dim_name_type_suite_ref = pd.read_csv(
        output_dir / 'previous_application' / 'dim_name_type_suite.csv'
    )
    print("  ✓ dim_name_type_suite (referencia: previous_application)")
    
    # ========================================================================
    # 2. CARGAR DATASETS Y CORREGIR application_train
    # ========================================================================
    print("\n2. Corrigiendo application_train...")
    application_train_path = output_dir / 'application_train' / 'application_train.csv'    
    application_train = pd.read_csv(application_train_path)
    
    # Convertir columnas ID a Int64
    for col in application_train.columns:
        if 'ID' in col:
            application_train[col] = application_train[col].astype('Int64')
    
    # Mapeos para application_train
    mappings_app_train = {
        'NAME_CONTRACT_TYPE_ID': {
            1: 2,  # Cash loans: 1 -> 2
            2: 3   # Revolving loans: 2 -> 3
        },
        'WEEKDAY_APPR_PROCESS_START_ID': {
            1: 3,  # WEDNESDAY: 1 -> 3
            2: 1,  # MONDAY: 2 -> 1
            3: 4,  # THURSDAY: 3 -> 4
            4: 7,  # SUNDAY: 4 -> 7
            5: 6,  # SATURDAY: 5 -> 6
            6: 5,  # FRIDAY: 6 -> 5
            7: 2   # TUESDAY: 7 -> 2
        },
        'NAME_TYPE_SUITE_ID': {
            1: 1,  # Unaccompanied: 1 -> 1
            2: 3,  # Family: 2 -> 3
            3: 2,  # Spouse, partner: 3 -> 2
            4: 4,  # Children: 4 -> 4
            5: 6,  # Other_A: 5 -> 6
            6: 5,  # Other_B: 6 -> 5
            7: 7   # Group of people: 7 -> 7
        }
    }
    
    for col_name, mapping in mappings_app_train.items():
        if col_name in application_train.columns:
            application_train[col_name] = application_train[col_name].replace(mapping)
            print(f"  ✓ {col_name} remapeado")
    
    # ========================================================================
    # 3. CARGAR DATASETS Y CORREGIR previous_application
    # ========================================================================
    print("\n3. Corrigiendo previous_application...")
    previous_application_path = output_dir / 'previous_application' / 'previous_application.csv'
    previous_application = pd.read_csv(previous_application_path)
    
    # Convertir columnas ID a Int64
    for col in previous_application.columns:
        if 'ID' in col:
            previous_application[col] = previous_application[col].astype('Int64')
    
    # Mapeos para previous_application
    mappings_prev_app = {
        'WEEKDAY_APPR_PROCESS_START_ID': {
            1: 6,  # SATURDAY: 1 -> 6
            2: 4,  # THURSDAY: 2 -> 4
            3: 2,  # TUESDAY: 3 -> 2
            4: 1,  # MONDAY: 4 -> 1
            5: 5,  # FRIDAY: 5 -> 5
            6: 7,  # SUNDAY: 6 -> 7
            7: 3   # WEDNESDAY: 7 -> 3
        }
    }
    
    # Aplicar mapeos
    for col_name, mapping in mappings_prev_app.items():
        if col_name in previous_application.columns:
            previous_application[col_name] = previous_application[col_name].replace(mapping)
            print(f"  ✓ {col_name} remapeado")
    
    # ========================================================================
    # 4. EXPORTAR DATOS CORREGIDOS Y DIMENSIONES DE REFERENCIA
    # ========================================================================
    print("\n4. Exportando datos corregidos y dimensiones de referencia...")
    
    # Crear directorio common_dims si no existe
    common_dims_dir = output_dir / 'common_dims'
    if not os.path.exists(common_dims_dir):
        os.makedirs(common_dims_dir)
    
    # Guardar datasets corregidos
    application_train.to_csv(application_train_path, index=False)
    print("  ✓ application_train.csv exportado")
    
    previous_application.to_csv(previous_application_path, index=False)
    print("  ✓ previous_application.csv exportado")
    
    # Guardar dimensiones de referencia
    dim_name_contract_type_ref.to_csv(output_dir / 'common_dims' / 'dim_name_contract_type.csv', index=False)
    print("  ✓ dim_name_contract_type.csv exportado")
    
    dim_weekday_appr_process_start_ref.to_csv(output_dir / 'common_dims' / 'dim_weekday_appr_process_start.csv', index=False)
    print("  ✓ dim_weekday_appr_process_start.csv exportado")
    
    dim_name_type_suite_ref.to_csv(output_dir / 'common_dims' / 'dim_name_type_suite.csv', index=False)
    print("  ✓ dim_name_type_suite.csv exportado")
    
    print(f"\nDatos corregidos guardados en: {output_dir}")


def main():
    """Función principal que ejecuta la normalización de todos los datasets."""
    
    # Configuración de rutas
    BASE_DIR = Path(__file__).resolve().parent # Obtiene la carpeta donde está el script, sin importar desde dónde lo lances
    data_path = BASE_DIR / ".." / ".." / "data" / "raw"
    output_dir = BASE_DIR / ".." / ".." / "data" / "db_input"

    # Datasets a procesar (sin application_train y previous_application)
    datasets_standard = [
        # 'application_test.csv',
        'bureau_balance.csv',
        'bureau.csv',
        'credit_card_balance.csv',
        'installments_payments.csv',
        'POS_CASH_balance.csv'
    ]
    
    # Datasets con correcciones de overlap
    datasets_overlap = [
        'application_train.csv',
        'previous_application.csv'
    ]

    print("\n" + "="*70)
    print("NORMALIZACIÓN DE BASE DE DATOS - SCRIPT DE EJECUCIÓN")
    print("="*70)

    # ========================================================================
    # 1. PROCESAR DATASETS ESTÁNDAR
    # ========================================================================
    print("\n--- FASE 1: NORMALIZACIÓN ESTÁNDAR ---")
    for csv_name in datasets_standard:
        try:
            normalize_dataset(csv_name, data_path, output_dir)
        except FileNotFoundError:
            print(f"⚠ Archivo no encontrado: {csv_name}")
        except Exception as e:
            print(f"✗ Error procesando {csv_name}: {str(e)}")
    
    # ========================================================================
    # 2. PROCESAR DATASETS CON OVERLAP (SIN EXPORTAR DIMENSIONES AÚN)
    # ========================================================================
    print("\n--- FASE 2: NORMALIZACIÓN CON CORRECCIONES DE OVERLAP ---")
    for csv_name in datasets_overlap:
        try:
            normalize_dataset(
                csv_name,
                data_path,
                output_dir,
                skip_dimension_export=True
            )
        except FileNotFoundError:
            print(f"⚠ Archivo no encontrado: {csv_name}")
        except Exception as e:
            print(f"✗ Error procesando {csv_name}: {str(e)}")
    
    # ========================================================================
    # 3. APLICAR CORRECCIONES DE OVERLAP
    # ========================================================================
    print("\n--- FASE 3: APLICACIÓN DE CORRECCIONES DE OVERLAP ---")
    try:
        apply_overlap_corrections(output_dir)
    except Exception as e:
        print(f"✗ Error en correcciones de overlap: {str(e)}")
    
    # ========================================================================
    # 4. LIMPIAR DIRECTORIOS TEMPORALES
    # ========================================================================
    print("\n--- FASE 4: LIMPIEZA DE ARCHIVOS TEMPORALES ---")
    try:
        # Obtener lista de archivos CSV que existen en common_dims
        common_dims_dir = output_dir / 'common_dims'
        if os.path.exists(common_dims_dir):
            common_dims_files = set(f for f in os.listdir(common_dims_dir) if f.endswith('.csv'))
            print(f"  Archivos de referencia encontrados en common_dims: {len(common_dims_files)}")
            
            # Para cada dataset overlap, eliminar los CSV de dimensiones que coinciden
            for dataset in datasets_overlap:
                table_name = dataset.replace('.csv', '')
                table_dir = output_dir / table_name
                
                if os.path.exists(table_dir):
                    # Buscar y eliminar archivos CSV de dimensiones que coincidan
                    for file in os.listdir(table_dir):
                        if file.endswith('.csv') and file in common_dims_files:
                            file_path = table_dir / file
                            os.remove(file_path)
                            print(f"  ✓ Archivo eliminado: {file} de {table_name}/")
        else:
            print(f"⚠ Directorio common_dims no encontrado")
    except Exception as e:
        print(f"⚠ Error en limpieza: {str(e)}")
    
    print("\n" + "="*70)
    print("NORMALIZACIÓN COMPLETADA")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
