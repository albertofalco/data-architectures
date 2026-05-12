"""
Script de depuración para control de contenido de tablas vs CSV.

Este script está diseñado para investigar discrepancias de integridad aislando
un subconjunto de datos. Utiliza las llaves primarias para crear un "sandbox"
manejable de N registros, evitando penalizaciones de memoria o sortings
pesados en MySQL.

Uso:
python test_dbinput_debug.py --table pos_cash_balance --sample-size 500000
"""

import os
import sys
import argparse
import json
import pandas as pd
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ============================================================================
# CONFIGURACION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')
DATA_PATH = BASE_DIR / 'data' / 'db_input'
KEYS_FILE = BASE_DIR / '02_database_connections' / 'utils' / 'keys.json'

pd.set_option('future.no_silent_downcasting', True)

def load_keys():
    if KEYS_FILE.exists():
        with open(KEYS_FILE) as f:
            keys_list = json.load(f)
        return {item['table_name'].lower(): item['pk'] for item in keys_list}
    return {}

KEYS_DATA = load_keys()

def get_db_engine():
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    dbname = os.getenv('DB_NAME')
    return create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{dbname}")

# ============================================================================
# FUNCIONES DE DEBUGGING
# ============================================================================

def get_hash(df):
    sha256 = hashlib.sha256()
    data = df.to_csv(index=False, header=False).encode('utf-8')
    sha256.update(data)
    return sha256.hexdigest()

def debug_table(engine, csv_path, table_name, pk_cols, sample_size=500000, export_diff=False):
    print(f"\n--- [DEBUG] Iniciando entorno de prueba para {table_name} ---")
    
    if not pk_cols:
        print(f"❌ PK no encontrada para {table_name}. Debugger requiere PKs.")
        return
        
    main_pk = pk_cols[0]
    print(f"  PK principal seleccionada: {main_pk}")

    # Obtener todas las columnas para asegurar un ordenamiento determinista
    df_dummy = pd.read_csv(csv_path, nrows=0)
    all_cols = list(df_dummy.columns)
    sort_cols = pk_cols + [col for col in all_cols if col not in pk_cols]
    
    # 1. Cargar subconjunto directo desde DB (muy rápido gracias al índice PK)
    print(f"  Cargando {sample_size} registros desde DB en memoria...")
    order_by_clause = ", ".join([f"`{col}`" for col in sort_cols])
    query = text(f"SELECT * FROM `{table_name}` ORDER BY {order_by_clause} LIMIT {sample_size}")
        
    with engine.connect() as conn:
        df_db = pd.read_sql(query, conn)
        
    # 2. Cargar y ordenar CSV completo en memoria para extraer la misma muestra
    print(f"  Cargando y ordenando CSV completo en memoria para extraer muestra...")
    df_csv_full = pd.read_csv(csv_path)
    df_csv = df_csv_full.sort_values(by=sort_cols).head(sample_size).copy()
    del df_csv_full # Liberamos la memoria del CSV completo inmediatamente
    
    print(f"  -> CSV records: {len(df_csv)} | DB records: {len(df_db)}")
    
    if len(df_csv) != len(df_db):
        print("  ⚠️ Advertencia: Discrepancia de filas en el subconjunto. Igualando tamaños al menor...")
        min_len = min(len(df_csv), len(df_db))
        df_csv = df_csv.head(min_len)
        df_db = df_db.head(min_len)
        
    # Asegurar un ordenamiento 100% determinista usando todas las columnas
    all_cols = list(df_csv.columns)
    sort_cols = pk_cols + [col for col in all_cols if col not in pk_cols]
    
    # 3. Ordenamiento global determinista final
    print("  Asegurando orden estricto de ambos conjuntos de datos...")
    df_csv = df_csv.sort_values(by=sort_cols, na_position='first').reset_index(drop=True)
    df_db = df_db.sort_values(by=sort_cols, na_position='first').reset_index(drop=True)
    
    # 5. Normalización rápida de tipos antes de pandas_assert
    df_db = df_db.astype(df_csv.dtypes)
    
    # 6. Comparación
    print("\n--- Resultados del Debugger ---")
    
    hash_csv = get_hash(df_csv)
    hash_db = get_hash(df_db)
    
    print(f"  CSV Hash: {hash_csv}")
    print(f"  DB Hash:  {hash_db}")
    
    if hash_csv == hash_db:
        print("  ✅ [HASH] MATCH EXACTO. No se encontraron discrepancias en el subconjunto.")
    else:
        print("  ❌ [HASH] NO MATCH. Discrepancia hallada dentro del subconjunto.")
        
    try:
        pd.testing.assert_frame_equal(df_csv, df_db, atol=0.0001, rtol=0.0001)
        print("  ✅ [PANDAS] MATCH EXACTO.")
    except AssertionError as e:
        print("\n  ❌ [PANDAS] Discrepancia detectada en los DataFrames:")
        print(f"  {e}")
        
        if export_diff:
            print("\n  Exportando filas con diferencias a diff_report.csv...")
            try:
                # Intentar encontrar las filas exactas donde difieren
                diff_mask = (df_csv != df_db) & ~(df_csv.isna() & df_db.isna())
                diff_rows_indices = diff_mask.any(axis=1)
                
                df_csv_diff = df_csv[diff_rows_indices].copy()
                df_csv_diff['ORIGIN'] = 'CSV'
                
                df_db_diff = df_db[diff_rows_indices].copy()
                df_db_diff['ORIGIN'] = 'DB'
                
                # Intercalar filas para ver el antes y despues facil
                report = pd.concat([df_csv_diff, df_db_diff]).sort_index()
                report.to_csv('diff_report.csv', index=False)
                print("  Reporte exportado exitosamente en el directorio raíz.")
            except Exception as ex:
                print(f"  Error exportando reporte: {ex}")

def main():
    parser = argparse.ArgumentParser(description="Test Debugger para DB vs CSV")
    parser.add_argument("--table", type=str, required=True, help="Nombre de la tabla a debugear")
    parser.add_argument("--sample-size", type=int, default=500000, help="Tamaño aproximado de la muestra (default: 500k)")
    parser.add_argument("--export-diff", action="store_true", help="Exporta diferencias a un CSV local")
    args = parser.parse_args()

    table_name = args.table.lower()
    
    archivos = list(DATA_PATH.rglob('*.csv'))
    dict_archivos = {archivo.stem.lower(): archivo for archivo in archivos}
    
    if table_name not in dict_archivos:
        print(f"Error: Tabla '{table_name}' no encontrada en la carpeta data/db_input.")
        sys.exit(1)
        
    csv_path = dict_archivos[table_name]
    pk_cols = KEYS_DATA.get(table_name, [])
    
    try:
        engine = get_db_engine()
        debug_table(engine, csv_path, table_name, pk_cols, sample_size=args.sample_size, export_diff=args.export_diff)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("\nDebugger finalizado.")

if __name__ == '__main__':
    main()