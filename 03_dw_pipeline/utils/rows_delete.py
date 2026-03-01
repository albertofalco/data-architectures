"""
Eliminación de registros de tablas.

Este script elimina los últimos registros agregados a las tablas
especificadas en el archivo de configuración config.yml.
"""

import sys
import os
import yaml
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv
from pathlib import Path

# Configuración de rutas
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
CONFIG_PATH = CURRENT_DIR / "config.yml"

# Cargar variables de entorno
if not ENV_PATH.exists():
    print(f"Error: No se encontró el archivo .env en {ENV_PATH}")
    sys.exit(1)
load_dotenv(ENV_PATH)

# Cargar configuración desde YAML
if not CONFIG_PATH.exists():
    print(f"Error: No se encontró el archivo de configuración en {CONFIG_PATH}")
    sys.exit(1)

try:
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
        target_list = config.get("target_tables", [])
        TARGET_TABLES = [
            (t["table_name"], t["limit"], t["order_col"]) for t in target_list
        ]
except Exception as e:
    print(f"Error al leer la configuración: {e}")
    sys.exit(1)

def get_db_connection():
    """
    Establece la conexión con la base de datos MySQL.
    
    Returns:
        engine: Objeto de conexión SQLAlchemy engine.
    """
    try:
        host = os.getenv("DB_HOST")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        dbname = os.getenv("DB_NAME")
        
        if not all([host, user, dbname]):
             print("Error: Faltan variables de entorno para la conexión a BD.")
             sys.exit(1)

        connection_url = f"mysql+mysqlconnector://{user}:{password}@{host}/{dbname}"
        print(f"\nConectando a la base de datos: {dbname}...\n")
        engine = create_engine(connection_url)
        return engine
    except Exception as e:
        print(f"Error al configurar la conexión: {e}")
        sys.exit(1)

def main():
    """
    Función principal que ejecuta el proceso de eliminación.
    
    Muestra una vista previa de los registros a eliminar y solicita confirmación
    antes de proceder.
    """
    engine = get_db_connection()
    
    # Verificar conexión
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        sys.exit(1)

    for table_name, limit, order_col in TARGET_TABLES:
        print(f"\n--- Preparando borrado para: {table_name} ---")
        
        if table_name not in existing_tables:
            print(f"Error: La tabla '{table_name}' no existe en la base de datos.")
            sys.exit(1)
            
        try:
            # 1. Consultar el rango a eliminar para confirmación
            query_preview = f"SELECT {order_col} FROM {table_name} ORDER BY {order_col} DESC LIMIT {limit}"
            df_preview = pd.read_sql(query_preview, engine)
            
            if df_preview.empty:
                print(f"No hay registros para eliminar en {table_name}.")
                sys.exit(1)
                
            count = len(df_preview)
            min_id = df_preview[order_col].min()
            max_id = df_preview[order_col].max()
            
            print(f"SE ELIMINARÁN {count} REGISTROS.")
            print(f"Tabla: {table_name}")
            print(f"Rango de {order_col} a eliminar: {min_id} (mínimo en selección) - {max_id} (máximo en selección)")
            print("NOTA: Se eliminarán los últimos registros agregados (orden descendente).")
            
            confirm = input("¿Está seguro de que desea continuar con el borrado? (s/n): ").strip().lower()
            
            if confirm != 's':
                print("Operación cancelada por el usuario.")
                sys.exit(0)
            
            # 2. Ejecutar borrado
            # MySQL permite ORDER BY y LIMIT en DELETE
            delete_query = text(f"DELETE FROM {table_name} ORDER BY {order_col} DESC LIMIT {limit}")
            
            with engine.begin() as conn:
                result = conn.execute(delete_query)
                print(f"Operación completada. Registros eliminados: {result.rowcount}")

        except Exception as e:
            print(f"Error durante el proceso de borrado de {table_name}: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
