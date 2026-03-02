"""
Script para control de contenido de tablas en bases de datos respecto a archivos planos.

Este script verifica que las tablas contenidas en la base de datos mantienen la integridad
de los datos comparándolos con los archivos fuente.

Las pruebas incluyen:
1. Validacion de nombres de tablas.
2. Validacion de estructura (shape).
3. Validacion de nobmres de columnas.
4. Comparación de valores.

"""

# ============================================================================
# IMPORTACION DE LIBRERIAS
# ============================================================================

import os
import sys
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

# ============================================================================
# FUNCIONES DE INTEGRIDAD
# ============================================================================

def verify_by_hashing(csv_path, table_name, connection, chunk_size=1000000):
    """
    Genera un hash MD5 de los datos por bloques para comparar integridad
    sin cargar todo el archivo en memoria.
    """
    print(f"--- [HASH] Verificando {table_name} ---")
    
    def get_hash_csv():
        """Calcula el hash SHA256 del archivo CSV procesándolo por bloques."""
        sha256 = hashlib.sha256()
        i = 0
        # Leemos el CSV en pedazos de texto para el hash
        for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
            # Convertimos el chunk a string para un hash consistente
            data = chunk.to_csv(index=False, header=False).encode('utf-8')
            sha256.update(data)
            i += 1
            if len(chunk) < chunk_size:
                print(f"  Procesado hash csv: {len(chunk)} registros...", end="\r")
            else:
                print(f"  Procesado hash csv: {i * chunk_size} registros...", end="\r")
        return sha256.hexdigest()

    def get_hash_db():
        sha256 = hashlib.sha256()
        # Consultamos la DB por offsets
        offset = 0
        i = 0
        while True:
            query = text(f"SELECT * FROM {table_name} LIMIT {chunk_size} OFFSET {offset}")
            chunk_db = pd.read_sql(query, connection)
            if chunk_db.empty:
                break
            data = chunk_db.to_csv(index=False, header=False).encode('utf-8')
            sha256.update(data)
            offset += chunk_size
            i += 1
            if len(chunk_db) < chunk_size:
                print(f"  Procesado hash db: {len(chunk_db)} registros...", end="\r")
            else:
                print(f"  Procesado hash db:  {i * chunk_size} registros...", end="\r")
        return sha256.hexdigest()

    hash_csv = get_hash_csv()
    hash_db = get_hash_db()

    if hash_csv == hash_db:
        print(f"✅ Hash coincide: {hash_csv}")
        return True
    else:
        print(f"❌ Hash NO coincide.")
        return False

def verify_by_chunks(csv_path, table_name, connection, chunk_size=1000000):
    """
    Compara el contenido fila a fila utilizando chunks y validación de Pandas.
    """
    print(f"--- [CHUNKS] Verificando {table_name} ---")
    csv_iter = pd.read_csv(csv_path, chunksize=chunk_size)
    
    offset = 0
    try:
        for i, df_csv in enumerate(csv_iter):
            query = text(f"SELECT * FROM {table_name} LIMIT {chunk_size} OFFSET {offset}")
            df_db = pd.read_sql(query, connection)
            
            # Normalización rápida: asegurar que los tipos coincidan (SQL suele traer tipos distintos)
            df_db = df_db.astype(df_csv.dtypes)

            # Asegurar que los índices coincidan para la comparación
            df_db.index = pd.RangeIndex(start=offset, stop=offset + len(df_db), step=1)

            pd.testing.assert_frame_equal(df_csv, df_db, atol=0.0001, rtol=0.0001)
            offset += chunk_size
            print(f"  Procesados {i * chunk_size + len(df_db)} registros...", end="\r")
            
        print(f"\n✅ Integridad total confirmada por bloques para {table_name}.")
    except AssertionError as e:
        print(f"\n❌ Discrepancia encontrada en el bloque que inicia en fila {offset}:")
        print(e)
    except Exception as e:
        print(f"\n❌ Error durante la comparación: {e}")

def control_table_names(connection, dir_path):
    result = connection.execute(text("SHOW TABLES"))
    db_names = {t[0].lower() for t in result.fetchall()}

    if not dir_path.exists():
        raise FileNotFoundError(f"Carpeta {dir_path} no existe.")

    archivos = list(dir_path.rglob('*.csv'))
    dict_archivos = {archivo.stem.lower(): archivo for archivo in archivos}
    csv_names = set(dict_archivos.keys())

    common_names = csv_names.intersection(db_names)
    return common_names, dict_archivos

# ============================================================================
# MAIN
# ============================================================================

def main():
    try:
        engine = create_engine(f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")
        connection = engine.connect()
        print(f"Conectado a la base de datos: '{os.getenv('DB_NAME')}'", end="\n")

        tables, dict_archivos = control_table_names(connection, DATA_PATH)
        
        print(f"Tablas comunes encontradas: {tables}", end="\n\n")
        
        i = 0
        for table in sorted(tables):
            # Filtro para tu tabla pesada específica
            # if 'dim' in table...
            csv_file = dict_archivos[table]
            
            # Opción 1: Hasheo (Muy rápido para descartar errores)
            print(f"\nProcesando tabla {table} ({i+1}/{len(tables)})...")
            verify_by_hashing(csv_file, table, connection)
            i += 1
            
            # Opción 2: Assert por Chunks (Lento pero detallado)
            # print(f"Procesando tabla {table} ({i+1}/{len(tables)})...")
            # print(f"\nVerificando integridad de {table} usando chunks...")
            # verify_by_chunks(csv_file, table, connection)
            # i += 1

    except Exception as e:
        print(f"Error: {e}")
    finally:
        connection.close()
        print("\nProceso finalizado.")

if __name__ == '__main__':
    main()