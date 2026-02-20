import sys
import os
import pandas as pd
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv
from pathlib import Path

# Configuración de rutas
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
ASSETS_DIR = CURRENT_DIR.parent / "assets"
ENV_PATH = PROJECT_ROOT / ".env"

# Cargar variables de entorno
if not ENV_PATH.exists():
    print(f"Error: No se encontró el archivo .env en {ENV_PATH}")
    sys.exit(1)
load_dotenv(ENV_PATH)

# Constantes definidas por requerimiento
TARGET_TABLES = [("application_train", 70000, "SK_ID_CURR")]

def get_db_connection():
    try:
        host = os.getenv("DB_HOST")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        dbname = os.getenv("DB_NAME")
        
        if not all([host, user, dbname]):
             print("Error: Faltan variables de entorno para la conexión a BD.")
             sys.exit(1)

        # Usar mysql-connector-python
        connection_url = f"mysql+mysqlconnector://{user}:{password}@{host}/{dbname}"
        engine = create_engine(connection_url)
        return engine
    except Exception as e:
        print(f"Error al configurar la conexión: {e}")
        sys.exit(1)

def main():
    engine = get_db_connection()
    
    # Verificar conexión
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        sys.exit(1)

    # Crear directorio assets si no existe
    if not ASSETS_DIR.exists():
        print(f"Creando directorio de assets: {ASSETS_DIR}")
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for table_name, limit, order_col in TARGET_TABLES:
        print(f"Procesando backup para: {table_name}")
        
        if table_name not in existing_tables:
            print(f"Error: La tabla '{table_name}' no existe en la base de datos.")
            sys.exit(1)
            
        try:
            # Obtener los últimos N registros (orden descendente)
            # Nota: Ordenamos descendente para obtener los últimos, pero el dataframe tendrá ese orden.
            query = f"SELECT * FROM {table_name} ORDER BY {order_col} DESC LIMIT {limit}"
            df = pd.read_sql(query, engine)
            
            if df.empty:
                print(f"Advertencia: No se encontraron registros para la tabla {table_name}.")
                sys.exit(1)
                
            # Verificar cantidad
            if len(df) < limit:
                print(f"Advertencia: Se solicitaron {limit} registros, pero solo se encontraron {len(df)}.")

            # Guardar en CSV
            output_file = ASSETS_DIR / f"{table_name}.csv"
            df.to_csv(output_file, index=False)
            
            # Obtener rango para feedback
            if order_col in df.columns:
                min_id = df[order_col].min()
                max_id = df[order_col].max()
                print(f"Backup exitoso. Archivo guardado en: {output_file}")
                print(f"Registros guardados: {len(df)}")
                print(f"Rango de {order_col} en backup: {min_id} - {max_id}")
            else:
                print(f"Backup exitoso. Archivo guardado en: {output_file}")
                print(f"Registros guardados: {len(df)}")
                print(f"Columna de referencia {order_col} no encontrada en el resultado.")

        except Exception as e:
            print(f"Error durante el backup de {table_name}: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
