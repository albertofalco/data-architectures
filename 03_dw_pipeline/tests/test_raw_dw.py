"""
Script de verificación de integridad de datos entre archivos CSV y tablas en ClickHouse.
Compara estructura (columnas) y contenido (datos) de tablas raw con sus fuentes CSV.
"""

import pandas as pd
import yaml
import os
import sys
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yml")
SRC_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../src/config.yml")
DATA_RAW_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "raw")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def load_src_config():
    with open(SRC_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def get_db_client():
    host = os.getenv("CLICKHOUSE_HOST", "localhost")
    port = int(os.getenv("CLICKHOUSE_PORT", "8123") or 8123)
    user = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "")
    return clickhouse_connect.get_client(host=host, port=port, username=user, password=password)

def get_db_table_name(table_name):
    return f"rep_{table_name}"

def check_table_integrity(table_info, config_data, src_config_data, db_client):
    table_name = table_info["name"]
    file_name = table_info["file_name"]
    
    print(f"\n{'='*40}")
    print(f"Tabla: {table_name}")
    print(f"{'='*40}")
    
    csv_path = os.path.join(DATA_RAW_PATH, file_name)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Archivo {csv_path} no encontrado")
    
    print(f"Cargando CSV: {csv_path}")
    # df = pd.read_csv(csv_path, keep_default_na=False, na_values=["", "NA", "N/A", "null", "NULL", "NaN"])
    df = pd.read_csv(csv_path, dtype_backend="numpy_nullable")

    # Normalizar valores vacíos y NaN para comparación consistente
    # df = df.replace("", pd.NA)
    # df = df.replace("NA", pd.NA)
    # df = df.replace("N/A", pd.NA)
    # df = df.replace("null", pd.NA)
    # df = df.replace("NULL", pd.NA)
    # df = df.replace("NaN", pd.NA)
    
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
    
    if ref_col:
        print(f"Ordenando por {ref_col}")
        df = df.sort_values(by=ref_col).reset_index(drop=True)
    
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
    
    # if not ref_col:
    #     print("[INFO] No se puede verificar contenido sin reference_column")
    #     return True
    
    print("Verificando contenido...")
    chunk_size = config_data.get("chunk_size", 100000)
    total_rows = len(df)
    
    compare_cols = sorted(csv_cols)
    cols_str = ", ".join(compare_cols)
    
    df = df[compare_cols]
    
    order_by_str = f"ORDER BY {', '.join(ref_col)}" if ref_col else ""
    
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
            
            # Normalizar valores None/NaN de la base de datos
            db_chunk_df = db_chunk_df.replace({None: pd.NA})
            for col in db_chunk_df.columns:
                db_chunk_df[col] = db_chunk_df[col].apply(lambda x: pd.NA if pd.isna(x) or x is None or x == "" or str(x).upper() in ["NA", "N/A", "NULL", "NAN"] else x)
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
    try:
        client = get_db_client()
        client.command("SELECT 1")
        return True, None
    except Exception as e:
        return False, str(e)

def main():
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
        
        print(f"Iniciando verificación de integridad para {len(transaction_tables)} tablas...")
        
        results = {}
        for table_info in transaction_tables:
            success = check_table_integrity(table_info, config_data, src_config_data, db_client)
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

if __name__ == "__main__":
    main()
