"""Compare normalized CSV files with their corresponding MySQL tables."""

# ==================== IMPORTS ====================

import os
import sys
import argparse
import json
import pandas as pd
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ==================== CONFIGURATION ====================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')
DATA_PATH = BASE_DIR / 'data' / 'db_input'
KEYS_FILE = BASE_DIR / '02_database_connections' / 'utils' / 'keys.json'

# ==================== HELPER FUNCTIONS ====================

def load_keys():
    """Load configured table keys indexed by lowercase table name."""
    if KEYS_FILE.exists():
        with open(KEYS_FILE) as f:
            keys_list = json.load(f)
        return {item['table_name'].lower(): item['pk'] for item in keys_list}
    return {}

KEYS_DATA = load_keys()

def verify_schema_and_shape(csv_path, table_name, connection):
    """Compare CSV and database column order and row counts."""
    print(f"--- [SCHEMA] Validando estructura de {table_name} ---")
    
    # Compare column names and order.
    df_csv_cols = pd.read_csv(csv_path, nrows=0).columns.tolist()
    query_cols = text(f"SELECT * FROM {table_name} LIMIT 0")
    df_db_cols = pd.read_sql(query_cols, connection).columns.tolist()
    
    if df_csv_cols != df_db_cols:
        print(f"❌ Error en nombres/orden de COLUMNAS.")
        print(f"   CSV: {df_csv_cols}")
        print(f"   DB:  {df_db_cols}")
        return False
    print("✅ Columnas coinciden")

    # Compare row counts.
    with open(csv_path, 'r', encoding='utf-8') as f:
        csv_rows = sum(1 for _ in f) - 1 # Restar header
        
    query_count = text(f"SELECT COUNT(*) FROM {table_name}")
    db_rows = connection.execute(query_count).scalar()
    
    if csv_rows != db_rows:
        print(f"❌ Error de SHAPE (Filas): CSV {csv_rows} vs DB {db_rows}")
        return False
    print(f"✅ Shape de filas coincide ({csv_rows})")
    
    return True

def verify_by_hashing(csv_path, table_name, connection, pk_cols=None, chunk_size=1000000):
    """Compare ordered CSV and database content with cumulative SHA-256 hashes."""
    print(f"--- [HASH] Verificando {table_name} ---")

    if not pk_cols:
        print(f"  ⚠️ PK no encontrada para {table_name}, omitiendo...")
        return None
    
    # Sort by primary keys and remaining columns for deterministic comparisons.
    df_cols_dummy = pd.read_csv(csv_path, nrows=0)
    all_cols = list(df_cols_dummy.columns)
    sort_cols = pk_cols + [col for col in all_cols if col not in pk_cols]
    
    def get_hash_csv():
        """Return the hash of the fully ordered CSV content."""
        sha256 = hashlib.sha256()
        print(f"  Cargando y ordenando CSV completo en memoria para hash...")
        df_full_csv = pd.read_csv(csv_path)
        
        # Match MySQL ordering by placing null values first.
        df_full_csv = df_full_csv.sort_values(by=sort_cols, na_position='first').reset_index(drop=True)
            
        for pos in range(0, len(df_full_csv), chunk_size):
            chunk = df_full_csv.iloc[pos:pos+chunk_size]
            data = chunk.to_csv(index=False, header=False).encode('utf-8')
            sha256.update(data)
            print(f"  Procesado hash csv: {pos + len(chunk)} registros...", end="\r")
        print()
        return sha256.hexdigest()

    def get_hash_db():
        """Return the hash of ordered database content read in chunks."""
        sha256 = hashlib.sha256()
        offset = 0
        order_by_clause = ", ".join([f"`{col}`" for col in sort_cols])
        
        while True:
            db_limit = chunk_size

            query = text(f"SELECT * FROM {table_name} ORDER BY {order_by_clause} LIMIT {db_limit} OFFSET {offset}")
            chunk_db = pd.read_sql(query, connection)
            if chunk_db.empty:
                break
            data = chunk_db.to_csv(index=False, header=False).encode('utf-8')
            sha256.update(data)
            offset += len(chunk_db)
            print(f"  Procesado hash db: {offset} registros...", end="\r")
        print()
        return sha256.hexdigest()

    hash_csv = get_hash_csv()
    hash_db = get_hash_db()

    if hash_csv == hash_db:
        print(f"✅ Hash coincide: {hash_csv}")
        return True
    else:
        print(f"❌ Hash NO coincide.")
        return False

def verify_by_pandas(csv_path, table_name, connection, pk_cols=None, chunk_size=1000000):
    """Compare ordered CSV and database rows with pandas."""
    print(f"--- [PANDAS] Verificando {table_name} ---")

    if not pk_cols:
        print(f"  ⚠️ PK no encontrada para {table_name}, omitiendo...")
        return None

    # Build deterministic ordering across all columns.
    df_cols_dummy = pd.read_csv(csv_path, nrows=0)
    all_cols = list(df_cols_dummy.columns)
    sort_cols = pk_cols + [col for col in all_cols if col not in pk_cols]
    
    order_by_clause = ", ".join([f"`{col}`" for col in sort_cols])
    
    print(f"  Cargando y ordenando CSV completo en memoria...")
    df_full_csv = pd.read_csv(csv_path)
    
    # Match MySQL ordering by placing null values first.
    df_full_csv = df_full_csv.sort_values(by=sort_cols, na_position='first').reset_index(drop=True)
    
    offset = 0
    try:
        for i in range(0, len(df_full_csv), chunk_size):
            df_csv = df_full_csv.iloc[i:i+chunk_size].copy()
            
            db_limit = min(chunk_size, len(df_csv))

            query = text(f"SELECT * FROM {table_name} ORDER BY {order_by_clause} LIMIT {db_limit} OFFSET {offset}")
            df_db = pd.read_sql(query, connection)
            
            # Align database types with the source DataFrame.
            df_db = df_db.astype(df_csv.dtypes)

            # Align indexes before comparison.
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

def control_table_names(connection, dir_path):
    """Compare normalized CSV filenames with database table names."""
    result = connection.execute(text("SHOW TABLES"))
    db_names = {t[0].lower() for t in result.fetchall()}

    if not dir_path.exists():
        raise FileNotFoundError(f"Carpeta {dir_path} no existe.")

    archivos = list(dir_path.rglob('*.csv'))
    dict_archivos = {archivo.stem.lower(): archivo for archivo in archivos}
    csv_names = set(dict_archivos.keys())

    common_names = csv_names.intersection(db_names)
    return common_names, dict_archivos

# ==================== MAIN FUNCTIONS ====================

def parse_args():
    """Parse command-line validation options."""
    parser = argparse.ArgumentParser(
        description="Verifica integridad de tablas MySQL contra archivos CSV fuente."
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
    return parser.parse_args()

def main():
    """Run normalized CSV integrity checks against MySQL."""
    args = parse_args()

    try:
        engine = create_engine(f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")
        connection = engine.connect()
        print(f"Conectado a la base de datos: '{os.getenv('DB_NAME')}'")

        tables, dict_archivos = control_table_names(connection, DATA_PATH)

        if args.table:
            target = args.table.lower()
            if target not in tables:
                print(f"\nTabla '{args.table}' no encontrada. Tablas disponibles: {sorted(tables)}")
                return
            tables = {target}

        print(f"Tablas a verificar: {sorted(tables)}\n")

        verify_fn = verify_by_hashing if args.method == "hashing" else verify_by_pandas

        for i, table in enumerate(sorted(tables), start=1):
            csv_file = dict_archivos[table]
            pk_cols = KEYS_DATA.get(table, [])
            print(f"\nProcesando tabla {table} ({i}/{len(tables)})...")
            
            # Validate schema and row count before comparing content.
            if not verify_schema_and_shape(csv_file, table, connection):
                print(f"⚠️ Omitiendo verificación profunda para {table} debido a fallos de estructura.")
                continue

            if args.schema_only:
                print(f"⏩ Omitiendo verificación de contenido para {table} (--schema-only).")
                continue

            verify_fn(csv_file, table, connection, pk_cols=pk_cols)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        connection.close()
        print("\nProceso finalizado.")

# ==================== EXECUTION ====================

if __name__ == '__main__':
    main()
