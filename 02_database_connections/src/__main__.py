"""Load normalized CSV files into MySQL tables."""

# ==================== IMPORTS ====================

import argparse
from getpass import getpass
import os
import sys
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import BigInteger, Integer, create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

# ==================== CONFIGURATION ====================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')
DATA_PATH = BASE_DIR / 'data' / 'db_input'

# ==================== MAIN FUNCTIONS ====================

def main():
    """Load all normalized CSV files into the configured MySQL database."""
    # Parse connection arguments.
    parser = argparse.ArgumentParser(description="Cargador de CSV a MySQL vía SQLAlchemy")
    parser.add_argument("--host", default=os.getenv('DB_HOST', '127.0.0.1'), help="Host de la base de datos")
    parser.add_argument("--user", default=os.getenv('DB_USER', 'root'), help="Usuario")
    parser.add_argument("--password", action="store_true", help="Solicitar contraseña de forma interactiva")
    parser.add_argument("--database", default=os.getenv('DB_NAME', ''), help="Nombre de la base de datos")
    
    args = parser.parse_args()
    password = getpass("Password: ") if args.password else os.getenv('DB_PASSWORD', '')

    # Create an SQLAlchemy engine without selecting a database.
    connection_url = URL.create(
        "mysql+mysqlconnector",
        username=args.user,
        password=password,
        host=args.host,
    )
    engine = create_engine(connection_url)

    # Create the database when needed.
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {args.database}"))
            conn.execute(text(f"USE {args.database}"))
        
        # Recreate the engine with the target database selected.
        db_url = URL.create(
            "mysql+mysqlconnector",
            username=args.user,
            password=password,
            host=args.host,
            database=args.database,
        )
        engine = create_engine(db_url)
        print(f"Conectado a la base de datos: '{args.database}'")
    except SQLAlchemyError as e:
        print(f"Error de conexión o creación de DB: {e}")
        return

    # Find all normalized CSV files recursively.
    if not DATA_PATH.exists():
        print(f"Error: La carpeta {DATA_PATH} no existe.")
        return

    archivos = list(DATA_PATH.rglob('*.csv'))

    for archivo in archivos:
        nombre_tabla = archivo.stem.lower()
        print(f"Procesando {archivo.name}...")

        try:
            # Read the normalized CSV.
            df = pd.read_csv(archivo, dtype_backend="numpy_nullable")
            
            # Map nullable pandas integers to SQLAlchemy integer columns.
            dtype_mapping = {}
            for col_name, col_type in df.dtypes.items():
                if str(col_type) == 'Int64' or str(col_type) == 'int64':
                    dtype_mapping[col_name] = Integer()
            print(f"Tipos detectados para '{archivo.name}': {dtype_mapping}")
            
            # Replace the destination table and load data in batches.
            df.to_sql(
                name=nombre_tabla, 
                con=engine, 
                if_exists='replace', 
                index=False,
                chunksize=1000,
                dtype=dtype_mapping
            )
            
            print(f"Tabla '{nombre_tabla}' cargada exitosamente ({len(df)} filas).")

        except Exception as e:
            print(f"Error procesando {archivo.name}: {e}")

    
    print("\nProceso completado.")

# ==================== EXECUTION ====================

if __name__ == '__main__':
    main()
