"""
Script para verificar la conexión a la base de datos.
"""

# ============================================================================
# IMPORTACION DE LIBRERIAS
# ============================================================================

import os
import sys
import mysql.connector
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ============================================================================
# CONFIGURACION DE VARIABLES
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')

# ============================================================================
# FUNCIONES
# ============================================================================

def mysql_connection():
    # Conexión a la base de datos
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )

        if conn.is_connected():
            print("Conexión exitosa a la base de datos usando mysql-connector-python.")
        else:
            print("No se pudo conectar a la base de datos con mysql-connector-python.")
        
        query = "SELECT * FROM application_train"
        # cursor = conn.cursor()
        # cursor.execute(query)
        # tables = cursor.fetchall()
        df = pd.read_sql(query, conn)
        print(f"Número de filas en la tabla application_train: {len(df)}")
        
    except Exception as e:
        print(f"Error de conexión con mysql-connector-python: {e}")
        sys.exit(1)

    finally:
        conn.close()
        print("\nProceso finalizado con mysql-connector-python.")

def sqlalchemy_connection():
    # Conexión a la base de datos    
    try:
        engine = create_engine(f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")
        with engine.connect() as connection:
            print("Conexión exitosa a la base de datos usando SQLAlchemy.")

            stmt = text("SELECT * FROM application_train")
            # result = connection.execute(stmt)
            # tables = result.fetchall()
            df = pd.read_sql(stmt, connection)
            print(f"Número de filas en la tabla application_train: {len(df)}")
    except Exception as e:
        print(f"Error de conexión con SQLAlchemy: {e}")
        sys.exit(1)
    finally:
        print("\nProceso finalizado con SQLAlchemy.")


def main():
    """Función principal para verificar la conexión a la base de datos."""
    print("Verificando conexión con mysql-connector-python...")
    mysql_connection()
    print("\nVerificando conexión con SQLAlchemy...")
    sqlalchemy_connection()

# ============================================================================
# EJECUCION PRINCIPAL
# ============================================================================

if __name__ == '__main__':
    main()