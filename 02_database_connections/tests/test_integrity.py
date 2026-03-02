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
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ============================================================================
# CONFIGURACION DE VARIABLES
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')
DATA_PATH = BASE_DIR / 'data' / 'db_input'

# ============================================================================
# FUNCIONES
# ============================================================================

def control_table_names(connection, dir_path):
    """Verifica que las tablas en la base de datos coincidan con los archivos CSV."""
    stmt = text("SHOW TABLES")
    result = connection.execute(stmt)
    tables = [t[0] for t in result.fetchall()]
    db_names = set(tables)

    if not dir_path.exists():
        raise FileNotFoundError(f"Error: La carpeta {dir_path} no existe.")

    archivos = list(dir_path.rglob('*.csv'))
    dict_archivos = {archivo.stem.lower(): archivo for archivo in archivos}
    csv_names = set(dict_archivos.keys())

    print("\n--- Control de nombres de tablas ---")
    print(f"Nombres en CSV: {csv_names}")
    print(f"Nombres en DB: {db_names}")

    if csv_names != db_names:
        missing_in_db = csv_names - db_names
        missing_in_csv = db_names - csv_names
        if missing_in_db: print(f"⚠️ Tablas en CSV pero no en DB: {missing_in_db}")
        if missing_in_csv: print(f"⚠️ Tablas en DB pero no en CSV: {missing_in_csv}")
    else:
        print("✅ Todos los nombres de tablas coinciden.")
    
    common_tables = csv_names.intersection(db_names)

    return common_tables, dict_archivos, tables

def control_shape_content(df_csv, df_db, tolerance=0.0001):
    
    # A. Control de Shape
    if df_csv.shape != df_db.shape:
        print(f"❌ Error de SHAPE: CSV {df_csv.shape} vs DB {df_db.shape}")
        return # Si el shape falla, los siguientes controles fallarán
    print(f"✅ Shape coincide {df_csv.shape}")

    # B. Control de nombres de columnas
    if list(df_csv.columns) != list(df_db.columns):
        print(f"❌ Error en nombres/orden de COLUMNAS.")
        return
    print("✅ Columnas coinciden")

    # C. Control de contenido (Valores)
    try:
        # np.allclose permite definir una tolerancia para floats
        # fillsna(0) o similar puede ser necesario según tus datos
        pd.testing.assert_frame_equal(df_csv, df_db, atol=tolerance, rtol=tolerance)
        print("✅ Contenido idéntico (dentro de la tolerancia)")
    except AssertionError as e:
        print(f"❌ Error en CONTENIDO: {e}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("Iniciando test de integridad de datos...")

    # Conexión a la base de datos    
    try:
        engine = create_engine(f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")
        connection = engine.connect()

        common_tables, dict_archivos, tables = control_table_names(connection, DATA_PATH)

        for table in list(common_tables):
            print(f"\n--- Analizando tabla: {table} ---")
            
            df_csv = pd.read_csv(dict_archivos[table])
            stmt = f"SELECT * FROM {table}"
            df_db = pd.read_sql(stmt, connection)

            control_shape_content(df_csv, df_db)

    except Exception as e:
        print(f"Error de conexión: {e}")
        sys.exit(1)

    finally:
        print("\nProceso finalizado.")
        connection.close()

if __name__ == '__main__':
    main()