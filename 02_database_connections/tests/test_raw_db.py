"""
Script de pruebas para la base de datos raw.
Valida la integridad y estructura de la base de datos cruda.
"""
import os
import sys
import json
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
    """Carga los metadatos de las tablas desde keys.json."""
    if not KEYS_FILE.exists():
        raise FileNotFoundError(f"No se encontró el archivo de claves en {KEYS_FILE}")
    with open(KEYS_FILE, 'r') as f:
        return json.load(f)

def get_table_metadata(keys_data, table_name):
    """Obtiene los metadatos (PKs, FKs) para una tabla específica."""
    for item in keys_data:
        if item['table_name'] == table_name:
            return item
    return None

def get_db_columns(engine, table_name):
    """Obtiene la lista de columnas de una tabla en la base de datos."""
    query = text(f"SELECT * FROM `{table_name}` LIMIT 0")
    with engine.connect() as conn:
        result = conn.execute(query)
        return list(result.keys())

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

def compute_hashes(df):
    """
    Calcula un hash para cada fila del DataFrame.
    Normaliza tipos para asegurar consistencia entre CSV y DB.
    """
    
    # 2. Convertir a tipos 'nullable' consistentes (Int64, Float64, String)
    # Esto maneja NaN vs None y int vs float
    try:
        df = df.convert_dtypes(dtype_backend="numpy_nullable")
    except Exception:
        # Fallback para versiones antiguas de pandas si es necesario
        df = df.convert_dtypes()

    # FIX: Forzar conversión de Float64 a Int64 si todos los valores son enteros.
    # Esto corrige el problema donde read_csv infiere Float64 por la presencia de NaNs.
    for col in df.select_dtypes(include=['Float64', 'float64']).columns:
        df[col] = df[col].round(4) # Redondear para evitar problemas de precisión en comparación de floats..
        try:
            # Si todos los valores no nulos son enteros (x % 1 == 0)
            if np.all(np.mod(df[col].dropna(), 1) == 0):
                df[col] = df[col].astype("Int64")
        except Exception:
            pass
    
    # 3. Calcular hash de la fila
    hashes = pd.util.hash_pandas_object(df, index=False)
    return hashes.tolist()

def compare_table(engine, keys_data, csv_path):
    table_name_csv = csv_path.stem
    table_name = table_name_csv.lower() # Convertir a minúsculas para coincidir con la DB
    print(f"\n--- Procesando: {table_name_csv} (DB: {table_name}) ---")
    
    # 1. Obtener Metadatos
    metadata = get_table_metadata(keys_data, table_name_csv)
    if not metadata:
        print(f"Skipping: No hay metadatos en keys.json para {table_name_csv}")
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
        query = build_reconstruction_query(table_name, expected_columns, db_cols, metadata)
    except Exception as e:
        print(f"Error inspeccionando DB para {table_name}: {e}")
        return

    # 4. Procesar y Hashear (Stream)
    CHUNK_SIZE = 100000
    db_hashes = []
    csv_hashes = []

    print("  -> Leyendo DB y calculando hashes...")
    try:
        # Leer DB en chunks
        with engine.connect() as conn:
            # Usar execution_options para stream results si es soportado
            for chunk in pd.read_sql_query(query, conn, chunksize=CHUNK_SIZE, dtype_backend="numpy_nullable"):
                # Asegurar que las columnas coinciden con el CSV
                chunk = chunk[expected_columns]
                
                # Drop de columnas específicas para 'application_train' antes de hash
                if table_name == "application_train":
                    if "ORGANIZATION_TYPE" in chunk.columns: chunk = chunk.drop(columns=["ORGANIZATION_TYPE"])
                    if "ORGANIZATION_TYPE_2" in chunk.columns: chunk = chunk.drop(columns=["ORGANIZATION_TYPE_2"])

                h = compute_hashes(chunk)
                db_hashes.extend(h)
                print(f"     Procesados {len(db_hashes)} registros DB...", end='\r')
    except Exception as e:
        print(f"\nError leyendo DB: {e}")
        return

    print(f"\n  -> Leyendo CSV y calculando hashes...")
    try:
        # Leer CSV en chunks
        # dtype_backend="numpy_nullable" asegura que los ints sean Int64 (compatibles con DB)
        with pd.read_csv(csv_path, chunksize=CHUNK_SIZE, dtype_backend="numpy_nullable") as reader:
            for chunk in reader:
                # Drop de columnas específicas para 'application_train' antes de hash
                if table_name == "application_train":
                    if "ORGANIZATION_TYPE" in chunk.columns: chunk = chunk.drop(columns=["ORGANIZATION_TYPE"])

                # Convertir a tipos consistentes antes de hash
                h = compute_hashes(chunk)
                csv_hashes.extend(h)
                print(f"     Procesados {len(csv_hashes)} registros CSV...", end='\r')
    except Exception as e:
        print(f"\nError leyendo CSV: {e}")
        return

    # 5. Comparar
    print("\n  -> Ordenando y comparando resultados...")
    
    n_db = len(db_hashes)
    n_csv = len(csv_hashes)
    
    if n_db != n_csv:
        print(f"  [FAIL] Diferencia de conteo de filas. DB: {n_db} vs CSV: {n_csv}")
        return

    # Ordenar hashes para comparar conjuntos (independiente del orden de filas)
    db_hashes.sort()
    csv_hashes.sort()

    if np.array_equal(db_hashes, csv_hashes):
        print(f"  [OK] Integridad verificada. {n_db} filas coinciden exactamente.")
    else:
        # Contar diferencias
        diff_count = sum(1 for d, c in zip(db_hashes, csv_hashes) if d != c)
        print(f"  [FAIL] Los datos no coinciden. {diff_count} filas diferentes (basado en hash ordenado).")

def main():
    print("Iniciando validación de integridad DB vs Raw CSV...")
    
    try:
        engine = get_db_engine()
        keys_data = load_keys()
    except Exception as e:
        print(f"Error de inicialización: {e}")
        sys.exit(1)

    # Buscar archivos CSV de transacciones
    # Filtramos: archivos que existen en keys.json y NO son dimensiones (dim_*)
    # También ignoramos archivos auxiliares que no son tablas
    ignored_files = ['HomeCredit_columns_description.csv', 'sample_submission.csv', 'application_test.csv']
    
    csv_files = []
    for f in DATA_RAW_DIR.glob('*.csv'):
        if f.name in ignored_files:
            continue
        if f.name.startswith('dim_'):
            continue
        csv_files.append(f)

    # Ordenar alfabéticamente
    csv_files.sort(key=lambda x: x.name)

    for csv_file in csv_files:
        # if csv_file.stem == "previous_application": # DEBUG: Solo probar con application_train para validar el proceso
        compare_table(engine, keys_data, csv_file)
        # else: # DEBUG: Solo probar con application_train para validar el proceso
        #     continue # DEBUG: Solo probar con application_train para validar el proceso

    print("\nValidación completada.")

if __name__ == "__main__":
    main()