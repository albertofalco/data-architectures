"""
Script para control de contenido de tablas reconstruidas en bases de datos respecto a archivos planos crudos (raw).

Este script verifica que los datos en la base de datos (incluso desglosados en tablas de dimensiones)
mantienen la integridad de la fuente original. Realiza los JOINs necesarios para "desnormalizar" la BD
antes de compararla con el archivo de la carpeta `data/raw`.

Las pruebas incluyen:
1. Validacion de la existencia de la tabla.
2. Validacion de esquema (shape y columnas).
3. Comparación de valores mediante reconstrucción (por hashing o pandas).

Uso:
python test_raw_db.py [--table NOMBRE_TABLA] [--method {hashing,pandas}] [--schema-only]

Ejemplos:
- Verificar todas las tablas (hashing por defecto):
  python test_raw_db.py
- Verificar solo estructura/esquema (sin leer todo el contenido):
  python test_raw_db.py --schema-only
- Verificar una tabla específica con método de pandas:
  python test_raw_db.py --table application_train --method pandas
"""

import os
import sys
import json
import hashlib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# --- CONFIGURACIÓN DE RUTAS ---
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent
ROOT_DIR = PROJECT_DIR.parent
DATA_RAW_DIR = ROOT_DIR / 'data' / 'raw'
KEYS_FILE = PROJECT_DIR / 'utils' / 'keys.json'
ENV_FILE = ROOT_DIR / '.env'

# Cargar variables de entorno
load_dotenv(ENV_FILE)

# Configuración de Pandas
pd.set_option('future.no_silent_downcasting', True)

def get_db_engine():
    """Crea la conexión a la base de datos usando variables de entorno."""
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    host = os.getenv('DB_HOST', '127.0.0.1')
    dbname = os.getenv('DB_NAME', 'home_credit')
    
    if not dbname:
        raise ValueError("La variable de entorno DB_NAME no está definida.")
        
    # Usar mysql-connector como driver
    url = f"mysql+mysqlconnector://{user}:{password}@{host}/{dbname}"
    return create_engine(url)

def load_keys():
    """Carga los metadatos de las tablas desde keys.json y estandariza a minúsculas."""
    if not KEYS_FILE.exists():
        raise FileNotFoundError(f"No se encontró el archivo de claves en {KEYS_FILE}")
    with open(KEYS_FILE, 'r') as f:
        keys_list = json.load(f)
    # Estandarizamos los nombres de las tablas para que la búsqueda sea case-insensitive
    # NOTA: Guardamos todo el objeto item porque test_raw_db.py necesita tanto 'pk' como 'fk'
    return {item['table_name'].lower(): item for item in keys_list}

def check_table_exists_in_db(engine, table_name):
    """Verifica si una tabla existe en la base de datos (case-insensitive)."""
    query = text("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = :db_name AND LOWER(TABLE_NAME) = LOWER(:table_name)
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"db_name": os.getenv('DB_NAME'), "table_name": table_name})
        return result.fetchone() is not None

def find_csv_for_table(data_dir, table_name):
    """Busca el archivo CSV correspondiente a una tabla (case-insensitive)."""
    table_name_lower = table_name.lower()
    for f in data_dir.glob('*.csv'):
        if f.stem.lower() == table_name_lower:
            return f
    return None

def get_table_metadata(keys_data, table_name):
    """Obtiene los metadatos (PKs, FKs) para una tabla específica (case-insensitive)."""
    # Como keys_data ya es un dict en minúsculas, basta con hacer .get()
    return keys_data.get(table_name.lower())

def get_db_columns(engine, table_name):
    """Obtiene la lista de columnas de una tabla en la base de datos."""
    query = text(f"SELECT * FROM `{table_name}` LIMIT 0")
    with engine.connect() as conn:
        result = conn.execute(query)
        return list(result.keys())

def verify_schema_and_shape(csv_path, table_name, engine, metadata, expected_columns, db_cols):
    """
    Realiza controles rápidos de columnas y cantidad de filas antes de comprobaciones profundas.
    """
    print(f"--- [SCHEMA] Validando estructura de {table_name} ---")
    
    # 1. Control de nombres/orden de columnas
    query_reconstruction = build_reconstruction_query(table_name, expected_columns, db_cols, metadata)
    query_cols = text(f"{query_reconstruction} LIMIT 0")
    
    with engine.connect() as conn:
        df_db_cols = pd.read_sql(query_cols, conn).columns.tolist()
        
    if expected_columns != df_db_cols:
        print(f"❌ Error en nombres/orden de COLUMNAS.")
        print(f"   CSV: {expected_columns}")
        print(f"   DB:  {df_db_cols}")
        return False
    print("✅ Columnas coinciden")

    # 2. Control de Shape (Filas)
    with open(csv_path, 'r', encoding='utf-8') as f:
        csv_rows = sum(1 for _ in f) - 1 # Restar header
        
    query_count = text(f"SELECT COUNT(*) FROM `{table_name}`")
    with engine.connect() as conn:
        db_rows = conn.execute(query_count).scalar()
    
    if csv_rows != db_rows:
        print(f"❌ Error de SHAPE (Filas): CSV {csv_rows} vs DB {db_rows}")
        return False
    print(f"✅ Shape de filas coincide ({csv_rows})")
    
    return True

def build_reconstruction_query(table_name, csv_columns, db_columns, metadata):
    """
    Construye una query SQL para reconstruir la tabla desnormalizada.
    Realiza JOINs con las tablas dimensionales para reemplazar IDs por valores.
    """
    selects = []
    joins = []
    joined_tables = set()

    # Iterar sobre las columnas esperadas en el CSV (target)
    for col in csv_columns:
        # CASO 1: La columna existe directamente en la tabla DB
        if col in db_columns:
            selects.append(f"t.`{col}`")
        
        # CASO 2: La columna es un valor que proviene de una dimensión
        # (e.g. CSV tiene 'NAME_CONTRACT_TYPE', DB tiene 'NAME_CONTRACT_TYPE_ID')
        else:
            fk_col = f"{col}_ID" # Asumimos convención estándar
            if fk_col in db_columns and fk_col in metadata['fk']:
                # Inferir nombre de tabla dimensión y columna valor
                # FK: NAME_CONTRACT_TYPE_ID -> Dim Table: dim_name_contract_type -> Val: NAME_CONTRACT_TYPE
                dim_table = f"dim_{col.lower()}"
                dim_alias = f"d_{col.lower()}"
                
                # Seleccionar el valor de la dimensión con el nombre original del CSV
                selects.append(f"{dim_alias}.`{col}`")
                
                # Agregar JOIN si no se ha agregado ya
                if dim_table not in joined_tables:
                    joins.append(
                        f"LEFT JOIN `{dim_table}` {dim_alias} "
                        f"ON t.`{fk_col}` = {dim_alias}.`{fk_col}`"
                    )
                    joined_tables.add(dim_table)
            else:
                # Si no se encuentra, seleccionar NULL o advertir (aquí seleccionamos NULL para no romper)
                print(f"   [WARN] Columna '{col}' no encontrada en DB ni reconstruible via FK.")
                selects.append(f"NULL as `{col}`")

    # Construir Query Final
    query = f"SELECT {', '.join(selects)} FROM `{table_name}` t {' '.join(joins)}"
    return query

def compute_chunk_hash_cumulative(df, hasher):
    try:
        df = df.convert_dtypes(dtype_backend="numpy_nullable")
    except Exception:
        df = df.convert_dtypes()
    for col in df.select_dtypes(include=['Float64', 'float64']).columns:
        df[col] = df[col].round(4)
        try:
            if np.all(np.mod(df[col].dropna(), 1) == 0):
                df[col] = df[col].astype("Int64")
        except Exception:
            pass
    for col in df.columns:
        # Reemplazar NAs por un valor constante string para evitar que cambien de formato o sean ignorados
        col_data = df[col].astype(object).fillna("NULL").to_numpy(dtype=str).tobytes()
        hasher.update(col_data)
    return hasher

def compare_table(engine, keys_data, csv_path, method="hashing", schema_only=False):
    table_name_csv = csv_path.stem
    table_name = table_name_csv.lower() # Convertir a minúsculas para coincidir con la DB
    print(f"\n--- Procesando: {table_name_csv} (DB: {table_name}) ---")
    
    # 1. Obtener Metadatos
    metadata = get_table_metadata(keys_data, table_name_csv)
    if not metadata:
        print(f"  ⚠️ Skipping: No hay metadatos en keys.json para {table_name_csv}")
        return

    # 2. Leer cabeceras del CSV para saber qué columnas esperar
    try:
        csv_header = pd.read_csv(csv_path, nrows=0)
        expected_columns = csv_header.columns.tolist()
    except Exception as e:
        print(f"Error leyendo CSV {csv_path}: {e}")
        return

    # 3. Construir Query de DB
    try:
        db_cols = get_db_columns(engine, table_name)
        
        if not verify_schema_and_shape(csv_path, table_name, engine, metadata, expected_columns, db_cols):
            print(f"⚠️ Omitiendo verificación profunda para {table_name} debido a fallos de estructura.")
            return
            
        if schema_only:
            print(f"⏩ Omitiendo verificación de contenido para {table_name} (--schema-only).")
            return
            
        base_query = build_reconstruction_query(table_name, expected_columns, db_cols, metadata)
    except Exception as e:
        print(f"Error inspeccionando DB para {table_name}: {e}")
        return

    # 4. Preparación del ordenamiento determinista
    pk_cols = metadata.get('pk', [])
    if not pk_cols:
        print(f"  ⚠️ PK no encontrada para {table_name}, omitiendo verificación de contenido...")
        return
        
    # Ordenar por PKs + el resto de las columnas del RAW, para que coincida entre pandas y el query
    sort_cols = pk_cols + [col for col in expected_columns if col not in pk_cols]
    
    # IMPORTANTE: MySQL ejecutará el ORDER BY sobre los valores originales (t.columna),
    # Solo podemos ordenar por las columnas que pertenecen a la tabla t (las de db_cols)
    # para evitar que MySQL haga un filesort masivo sobre las dimensiones (JOINs).
    valid_db_order_cols = [c for c in sort_cols if c in db_cols]
    db_order_clause = ", ".join([f"t.`{c}`" for c in valid_db_order_cols])

    CHUNK_SIZE = 500000

    if method == "hashing":
        print(f"--- [HASH] Verificando {table_name} ---")
        
        def get_hash_csv():
            sha256 = hashlib.sha256()
            print(f"  Cargando y ordenando CSV en memoria para hash...")
            # Leer en chunk para memoria justa, aunque Pandas en 12GB debería soportar el archivo de ~700MB.
            df_full_csv = pd.read_csv(csv_path, dtype_backend="numpy_nullable")
            
            # Limpiezas específicas
            if table_name == "application_train" and "ORGANIZATION_TYPE" in df_full_csv.columns: 
                df_full_csv = df_full_csv.drop(columns=["ORGANIZATION_TYPE"])
                
            # Igualamos comportamiento de MySQL (NULLs al inicio)
            valid_sort_cols = [c for c in sort_cols if c in df_full_csv.columns]
            df_full_csv = df_full_csv.sort_values(by=valid_sort_cols, na_position='first').reset_index(drop=True)
            
            for pos in range(0, len(df_full_csv), CHUNK_SIZE):
                chunk = df_full_csv.iloc[pos:pos+CHUNK_SIZE].copy()
                sha256 = compute_chunk_hash_cumulative(chunk, sha256)
                print(f"  Procesado hash csv: {pos + len(chunk)} registros...", end="\r")
            print()
            return sha256.hexdigest()

        def get_hash_db():
            sha256 = hashlib.sha256()
            offset = 0
            
            with engine.connect() as conn:
                while True:
                    query_paginated = text(f"{base_query} ORDER BY {db_order_clause} LIMIT {CHUNK_SIZE} OFFSET {offset}")
                    chunk_db = pd.read_sql_query(query_paginated, conn, dtype_backend="numpy_nullable")
                    if chunk_db.empty:
                        break
                        
                    if table_name == "application_train":
                        if "ORGANIZATION_TYPE" in chunk_db.columns: chunk_db = chunk_db.drop(columns=["ORGANIZATION_TYPE"])
                        if "ORGANIZATION_TYPE_2" in chunk_db.columns: chunk_db = chunk_db.drop(columns=["ORGANIZATION_TYPE_2"])
                        
                    sha256 = compute_chunk_hash_cumulative(chunk_db, sha256)
                    offset += len(chunk_db)
                    print(f"  Procesado hash db: {offset} registros...", end="\r")
            print()
            return sha256.hexdigest()
            
        hash_csv = get_hash_csv()
        hash_db = get_hash_db()
        
        if hash_csv == hash_db:
            print(f"✅ Hash coincide: {hash_csv}")
        else:
            print(f"❌ Hash NO coincide.")
            
    elif method == "pandas":
        print(f"--- [PANDAS] Verificando {table_name} ---")
        
        print(f"  Cargando y ordenando CSV completo en memoria...")
        df_full_csv = pd.read_csv(csv_path)
        
        # Limpieza para application_train si aplica
        if table_name == "application_train" and "ORGANIZATION_TYPE" in df_full_csv.columns:
            df_full_csv = df_full_csv.drop(columns=["ORGANIZATION_TYPE"])
            
        valid_sort_cols = [c for c in sort_cols if c in df_full_csv.columns]
        df_full_csv = df_full_csv.sort_values(by=valid_sort_cols, na_position='first').reset_index(drop=True)
        
        offset = 0
        try:
            with engine.connect() as conn:
                for pos in range(0, len(df_full_csv), CHUNK_SIZE):
                    df_csv = df_full_csv.iloc[pos:pos+CHUNK_SIZE].copy()
                    
                    db_limit = len(df_csv)
        
                    query_paginated = text(f"{base_query} ORDER BY {db_order_clause} LIMIT {db_limit} OFFSET {offset}")
                    df_db = pd.read_sql_query(query_paginated, conn)
                    
                    if table_name == "application_train":
                        if "ORGANIZATION_TYPE" in df_db.columns: df_db = df_db.drop(columns=["ORGANIZATION_TYPE"])
                        if "ORGANIZATION_TYPE_2" in df_db.columns: df_db = df_db.drop(columns=["ORGANIZATION_TYPE_2"])
                    
                    # Alinear columnas por si acaso los dropeos las desajustan
                    df_csv = df_csv[df_db.columns]
                    
                    df_db = df_db.astype(df_csv.dtypes)
                    df_db.index = pd.RangeIndex(start=offset, stop=offset + len(df_db), step=1)
                    df_csv.index = pd.RangeIndex(start=offset, stop=offset + len(df_csv), step=1)
        
                    pd.testing.assert_frame_equal(df_csv, df_db, atol=0.0001, rtol=0.0001)
                    offset += len(df_csv)
                    print(f"  Procesados {offset} registros...", end="\r")
                    
                print(f"\n✅ Integridad total confirmada por bloques para {table_name}.")
        except AssertionError as e:
            print(f"\n❌ Discrepancia encontrada en el bloque que inicia en fila {offset}:")
            print(e)
        except Exception as e:
            print(f"\n❌ Error durante la comparación: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Verifica integridad de tablas MySQL reconstruidas contra archivos CSV fuente raw (crudos)."
    )
    parser.add_argument(
        "--table",
        type=str,
        default=None,
        help="Nombre de una tabla específica a verificar (sin --table se procesan todas)."
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["hashing", "pandas"],
        default="hashing",
        help="Método de verificación: 'hashing' (rápido, por defecto) o 'pandas' (detallado)."
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Realiza solo verificacion de estructura (shape y columnas) sin revisar el contenido."
    )
    args = parser.parse_args()

    print("Iniciando validación de integridad DB vs Raw CSV...")

    try:
        engine = get_db_engine()
        keys_data = load_keys()
    except Exception as e:
        print(f"Error de inicialización: {e}")
        sys.exit(1)

    ignored_files = ['HomeCredit_columns_description.csv', 'sample_submission.csv', 'application_test.csv']

    csv_files = []
    for f in DATA_RAW_DIR.glob('*.csv'):
        if f.name in ignored_files:
            continue
        if f.name.startswith('dim_'):
            continue
        csv_files.append(f)

    if args.table:
        table_name_input = args.table

        if not check_table_exists_in_db(engine, table_name_input):
            print(f"[ERROR] La tabla '{table_name_input}' no existe en la base de datos.")
            sys.exit(1)

        csv_path = find_csv_for_table(DATA_RAW_DIR, table_name_input)
        if not csv_path:
            print(f"[ERROR] No se encontró archivo CSV para la tabla '{table_name_input}'.")
            sys.exit(1)

        csv_files = [csv_path]
        print(f"Solo se validará la tabla: {table_name_input}")
    else:
        csv_files.sort(key=lambda x: x.name)

    for csv_file in csv_files:
        compare_table(engine, keys_data, csv_file, method=args.method, schema_only=args.schema_only)

    print("\nValidación completada.")

if __name__ == "__main__":
    main()