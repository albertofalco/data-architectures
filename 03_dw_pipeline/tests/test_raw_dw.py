"""Compare raw CSV schemas and content with ClickHouse report tables."""

# ==================== IMPORTS ====================

import pandas as pd
import numpy as np
import yaml
import os
import sys
import argparse
import hashlib
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

# ==================== CONFIGURATION ====================

pd.set_option("future.no_silent_downcasting", True)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yml")
SRC_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../src/config.yml")
DATA_RAW_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "raw")

# ==================== HELPER FUNCTIONS ====================

def load_config():
    """Load the local validation configuration."""
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def load_src_config():
    """Load the source pipeline configuration."""
    with open(SRC_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def get_db_client():
    """Create and return a ClickHouse client."""
    host = os.getenv("CLICKHOUSE_HOST", "localhost")
    port = int(os.getenv("CLICKHOUSE_PORT", "8123") or 8123)
    user = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "")
    return clickhouse_connect.get_client(host=host, port=port, username=user, password=password)

def get_db_table_name(table_name):
    """Return the report table name for a source table."""
    return f"rep_{table_name}"

def quote_identifier(identifier):
    """Quote a ClickHouse identifier."""
    return f"`{identifier}`"

def build_order_by_clause(columns):
    """Build deterministic ordering consistent with pandas."""
    if not columns:
        return ""
    order_cols = [f"{quote_identifier(col)} ASC NULLS FIRST" for col in columns]
    return f"ORDER BY {', '.join(order_cols)}"

def normalize_null_values(df):
    """Normalize common null representations before comparison."""
    df = df.replace({None: pd.NA})
    null_tokens = {"", "NA", "N/A", "NULL", "NAN"}
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: pd.NA
            if pd.isna(x) or x is None or (isinstance(x, str) and x.strip().upper() in null_tokens)
            else x
        )
    return df

def normalize_for_hash(df):
    """Normalize types and values for stable cross-system hashes."""
    df = normalize_null_values(df.copy())
    try:
        df = df.convert_dtypes(dtype_backend="numpy_nullable")
    except Exception:
        df = df.convert_dtypes()

    for col in df.select_dtypes(include=["Float64", "float64"]).columns:
        df[col] = df[col].round(4)
        try:
            non_null = df[col].dropna()
            if len(non_null) > 0 and np.all(np.mod(non_null, 1) == 0):
                df[col] = df[col].astype("Int64")
        except Exception:
            pass
    return df

def compute_chunk_hash_cumulative(df, hasher):
    """Update a cumulative hash with normalized DataFrame content."""
    df = normalize_for_hash(df)
    for col in df.columns:
        col_data = df[col].astype(object).fillna("NULL").to_numpy(dtype=str).tobytes()
        hasher.update(col_data)
    return hasher

def hash_dataframe_by_chunks(df, chunk_size):
    """Hash an ordered DataFrame in chunks."""
    sha256 = hashlib.sha256()
    for pos in range(0, len(df), chunk_size):
        chunk = df.iloc[pos : pos + chunk_size].copy()
        sha256 = compute_chunk_hash_cumulative(chunk, sha256)
        print(f"  Procesado hash csv: {pos + len(chunk)} registros...", end="\r")
    print()
    return sha256.hexdigest()

def hash_clickhouse_query_by_chunks(db_client, db_name, db_table, compare_cols, order_by_str, total_rows, chunk_size):
    """Hash a deterministically ordered ClickHouse table in chunks."""
    sha256 = hashlib.sha256()
    cols_str = ", ".join(quote_identifier(col) for col in compare_cols)

    for offset in range(0, total_rows, chunk_size):
        query = f"""
        SELECT {cols_str}
        FROM {db_name}.{db_table}
        {order_by_str}
        LIMIT {chunk_size} OFFSET {offset}
        """
        try:
            result = db_client.query(query)
            db_chunk_df = pd.DataFrame(result.result_rows, columns=compare_cols)
        except Exception as e:
            raise RuntimeError(f"Error al consultar datos de la tabla: {e}")

        sha256 = compute_chunk_hash_cumulative(db_chunk_df, sha256)
        print(f"  Procesado hash db: {offset + len(db_chunk_df)} registros...", end="\r")
    print()
    return sha256.hexdigest()

# ==================== MAIN FUNCTIONS ====================

def check_table_integrity(table_info, config_data, src_config_data, db_client, method="hashing", schema_only=False):
    """Compare table existence, row count, columns, and content with a source CSV."""
    table_name = table_info["name"]
    file_name = table_info["file_name"]
    
    print(f"\n{'='*40}")
    print(f"Tabla: {table_name}")
    print(f"{'='*40}")
    
    csv_path = os.path.join(DATA_RAW_PATH, file_name)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Archivo {csv_path} no encontrado")
    
    print(f"Cargando CSV: {csv_path}")

    df = pd.read_csv(csv_path, dtype_backend="numpy_nullable")
    
    ref_col = table_info.get("reference_column")
    if ref_col and isinstance(ref_col, str):
        ref_col = [ref_col]
    
    filter_col = ref_col[0] if ref_col else None
    
    if "excluded_first_entry" in table_info or "excluded_last_entry" in table_info:
        if not filter_col:
            raise ValueError(f"reference_column es requerido para {table_name} si se define excluded_first_entry o excluded_last_entry")
        
        if "excluded_first_entry" in table_info and "excluded_last_entry" not in table_info:
            start = table_info["excluded_first_entry"]
            print(f"Excluyendo registros donde {filter_col} >= {start}")
            df = df[df[filter_col] < start]
        elif "excluded_last_entry" in table_info and "excluded_first_entry" not in table_info:
            end = table_info["excluded_last_entry"]
            print(f"Excluyendo registros donde {filter_col} <= {end}")
            df = df[df[filter_col] > end]
        else:
            start = table_info["excluded_first_entry"]
            end = table_info["excluded_last_entry"]
            print(f"Excluyendo registros donde {filter_col} está entre {start} y {end}")
            df = df[~((df[filter_col] >= start) & (df[filter_col] <= end))]
    
    db_name = src_config_data["databases"]["storage_db"]
    db_table = get_db_table_name(table_name)
    
    exists_query = f"EXISTS TABLE {db_name}.{db_table}"
    try:
        if not db_client.command(exists_query):
            raise RuntimeError(f"La tabla {db_name}.{db_table} no existe en ClickHouse")
    except Exception as e:
        raise RuntimeError(f"Error al verificar si la tabla existe: {e}")
    
    print("Verificando cantidad de filas...")
    count_query = f"SELECT count() FROM {db_name}.{db_table}"
    try:
        db_count = db_client.command(count_query)
    except Exception as e:
        raise RuntimeError(f"Error al obtener conteo de filas: {e}")
    
    if len(df) != db_count:
        print(f"[DIFERENCIA] La cantidad de filas no coincide: CSV={len(df)}, DB={db_count}")
        return False
    print(f"[SIN DIFERENCIAS] Cantidad de filas verificada: {db_count}")
    
    print("Verificando columnas...")
    global_excluded_cols = config_data.get("excluded_columns", [])
    table_excluded_cols = table_info.get("excluded_columns", [])
    excluded_cols = list(set(global_excluded_cols + table_excluded_cols))
    
    desc_query = f"DESCRIBE TABLE {db_name}.{db_table}"
    try:
        db_cols_info = db_client.query(desc_query).result_rows
    except Exception as e:
        raise RuntimeError(f"Error al obtener columnas de la tabla: {e}")
    
    db_cols = [row[0] for row in db_cols_info if row[0] not in excluded_cols]
    csv_cols = [col for col in df.columns if col not in excluded_cols]
    
    if sorted(csv_cols) != sorted(db_cols):
        print(f"[DIFERENCIA] Las columnas no coinciden.\nCSV: {sorted(csv_cols)}\nDB: {sorted(db_cols)}")
        return False
    print("[SIN DIFERENCIAS] Columnas verificadas.")

    if schema_only:
        print(f"[SIN DIFERENCIAS] Esquema verificado para {table_name}.")
        return True
    
    print("Verificando contenido...")
    chunk_size = config_data.get("chunk_size", 100000)
    total_rows = len(df)
    
    compare_cols = sorted(csv_cols)
    cols_str = ", ".join(quote_identifier(col) for col in compare_cols)
    
    df = df[compare_cols]
    print(f"Ordenando por todas las columnas comparables ({len(compare_cols)} columnas)")
    df = df.sort_values(by=compare_cols, na_position="first").reset_index(drop=True)
    
    order_by_str = build_order_by_clause(compare_cols)

    if method == "hashing":
        print(f"--- [HASH] Verificando {table_name} ---")
        hash_csv = hash_dataframe_by_chunks(df, chunk_size)
        hash_db = hash_clickhouse_query_by_chunks(
            db_client,
            db_name,
            db_table,
            compare_cols,
            order_by_str,
            total_rows,
            chunk_size,
        )

        if hash_csv == hash_db:
            print(f"[SIN DIFERENCIAS] Hash coincide para {table_name}: {hash_csv}")
            return True

        print(f"[DIFERENCIA] Hash NO coincide para {table_name}. CSV={hash_csv}, DB={hash_db}")
        return False
    
    all_chunks_pass = True
    for i in range(0, total_rows, chunk_size):
        chunk_end = min(i + chunk_size, total_rows)
        print(f"\rAnalizando registros {chunk_end} de {total_rows}...")
        chunk_df = df.iloc[i : i + chunk_size].reset_index(drop=True)
        
        query = f"""
        SELECT {cols_str}
        FROM {db_name}.{db_table}
        {order_by_str}
        LIMIT {chunk_size} OFFSET {i}
        """
        try:
            result = db_client.query(query)
            db_chunk_df = pd.DataFrame(result.result_rows, columns=compare_cols)
            
            db_chunk_df = normalize_null_values(db_chunk_df)
        except Exception as e:
            raise RuntimeError(f"Error al consultar datos de la tabla: {e}")
        
        try:
            pd.testing.assert_frame_equal(chunk_df, db_chunk_df, check_dtype=False, rtol=1e-5, check_exact=False)
        except AssertionError as e:
            print(f"[DIFERENCIA] Diferencia encontrada en chunk starting at {i}")
            all_chunks_pass = False
            continue
            
    if all_chunks_pass:
        print(f"[SIN DIFERENCIAS] Contenido verificado para {table_name}.")
        return True
    else:
        return False

def check_db_connection():
    """Verify the ClickHouse connection."""
    try:
        client = get_db_client()
        client.command("SELECT 1")
        return True, None
    except Exception as e:
        return False, str(e)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Verifica integridad de tablas ClickHouse rep_* contra archivos CSV raw."
    )
    parser.add_argument(
        "--table",
        type=str,
        default=None,
        help="Nombre de una tabla específica a verificar (sin --table se procesan todas).",
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["hashing", "pandas"],
        default="hashing",
        help="Método de verificación de contenido: 'hashing' (por defecto) o 'pandas'.",
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Realiza solo verificación de existencia, filas y columnas sin revisar contenido.",
    )
    return parser.parse_args()

def main():
    """Run integrity validation for the selected report tables."""
    args = parse_args()

    print("Verificando conexión con ClickHouse...")
    
    connected, error_msg = check_db_connection()
    if not connected:
        print(f"\n[ERROR] No se pudo conectar al servidor ClickHouse: {error_msg}")
        print("Finalizando script.")
        sys.exit(1)
    
    print("[OK] Conexión con ClickHouse establecida.")
    
    try:
        config_data = load_config()
        src_config_data = load_src_config()
        db_client = get_db_client()
        
        transaction_tables = config_data["transaction_tables"]

        if args.table:
            matching_tables = [
                table_info
                for table_info in transaction_tables
                if table_info["name"].lower() == args.table.lower()
            ]
            if not matching_tables:
                print(f"\n[ERROR] La tabla '{args.table}' no existe en {CONFIG_PATH}.")
                available_tables = sorted(table_info["name"] for table_info in transaction_tables)
                print(f"Tablas disponibles: {available_tables}")
                sys.exit(1)
            transaction_tables = matching_tables
            print(f"Solo se validará la tabla: {transaction_tables[0]['name']}")
        
        print(f"Iniciando verificación de integridad para {len(transaction_tables)} tablas...")
        
        results = {}
        for table_info in transaction_tables:
            success = check_table_integrity(
                table_info,
                config_data,
                src_config_data,
                db_client,
                method=args.method,
                schema_only=args.schema_only,
            )
            results[table_info["name"]] = "PASS" if success else "FAIL"
            
        print("\n" + "="*40)
        print("RESUMEN")
        print("="*40)
        all_passed = True
        for name, status in results.items():
            print(f"{name}: {status}")
            if status == "FAIL":
                all_passed = False
        
        if all_passed:
            print("\nTODOS LOS TESTS PASARON")
            exit(0)
        else:
            print("\nALGUNOS TESTS FALLARON")
            exit(1)
            
    except Exception as e:
        print(f"\n[ERROR CRÍTICO] La ejecución falló: {e}")
        raise

# ==================== EXECUTION ====================

if __name__ == "__main__":
    main()
