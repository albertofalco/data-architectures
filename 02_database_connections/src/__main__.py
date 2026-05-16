#######################################################
# Script para cargar archivos CSV en una base de datos MySQL.
#######################################################

# Importacion de librerias.
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

#######################################################
# CONFIGURACIÓN
#######################################################

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')
DATA_PATH = BASE_DIR / 'data' / 'db_input'

######################################################
# FUNCIONES PRINCIPALES
######################################################

def main():
    """Ejecuta el proceso principal de carga de datos a MySQL."""
    # 1. Configuración de argumentos
    parser = argparse.ArgumentParser(description="Cargador de CSV a MySQL vía SQLAlchemy")
    parser.add_argument("--host", default=os.getenv('DB_HOST', '127.0.0.1'), help="Host de la base de datos")
    parser.add_argument("--user", default=os.getenv('DB_USER', 'root'), help="Usuario")
    parser.add_argument("--password", action="store_true", help="Solicitar contraseña de forma interactiva")
    parser.add_argument("--database", default=os.getenv('DB_NAME', ''), help="Nombre de la base de datos")
    
    args = parser.parse_args()
    password = getpass("Password: ") if args.password else os.getenv('DB_PASSWORD', '')

    # 2. Crear el Engine de SQLAlchemy
    connection_url = URL.create(
        "mysql+mysqlconnector",
        username=args.user,
        password=password,
        host=args.host,
    )
    engine = create_engine(connection_url)

    # 3. Verificar/Crear la base de datos
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {args.database}"))
            conn.execute(text(f"USE {args.database}"))
        
        # Re-creamos el engine apuntando directamente a la base de datos.
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

    # 4. Procesar archivos CSV
    if not DATA_PATH.exists():
        print(f"Error: La carpeta {DATA_PATH} no existe.")
        return

    archivos = list(DATA_PATH.rglob('*.csv'))

    for archivo in archivos:
        nombre_tabla = archivo.stem.lower()
        print(f"Procesando {archivo.name}...")

        try:
            # Leer CSV con Pandas
            df = pd.read_csv(archivo, dtype_backend="numpy_nullable")
            
            # Definir diccionarios de tipos manuales si es necesario
            # Pero una forma automática de "arreglar" los Int64 para SQLAlchemy es:
            dtype_mapping = {}
            for col_name, col_type in df.dtypes.items():
                if str(col_type) == 'Int64' or str(col_type) == 'int64':
                    dtype_mapping[col_name] = Integer() # O BigInteger() si son muy grandes
            print(f"Tipos detectados para '{archivo.name}': {dtype_mapping}")
            
            # 5. Cargar en MySQL usando Pandas + SQLAlchemy
            # 'if_exists="replace"' elimina la tabla y la crea de nuevo con los tipos correctos.
            # 'index=False' evita que Pandas cree una columna para el índice del DataFrame.
            # 'chunksize' ayuda si los archivos son muy grandes.
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

######################################################
# EJECUCIÓN PRINCIPAL
######################################################

if __name__ == '__main__':
    main()
