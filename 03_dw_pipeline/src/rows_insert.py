import sys
import os
import argparse
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

def get_db_connection():
    try:
        host = os.getenv("DB_HOST")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        dbname = os.getenv("DB_NAME")
        
        if not all([host, user, dbname]):
             print("Error: Faltan variables de entorno para la conexión a BD.")
             sys.exit(1)

        connection_url = f"mysql+mysqlconnector://{user}:{password}@{host}/{dbname}"
        engine = create_engine(connection_url)
        return engine
    except Exception as e:
        print(f"Error al configurar la conexión: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Insertar registros desde CSV de backup.")
    parser.add_argument("table", help="Nombre de la tabla")
    parser.add_argument("rows", type=int, help="Número de registros a insertar")
    parser.add_argument("col", help="Columna de referencia (para mostrar rango)")
    
    args = parser.parse_args()
    
    table_name = args.table
    num_rows = args.rows
    ref_col = args.col
    
    # 1. Verificar archivo CSV
    # El archivo debe coincidir con el nombre de la tabla
    csv_path = ASSETS_DIR / f"{table_name}.csv"
    if not csv_path.exists():
        print(f"Error: No se encuentra el archivo de backup en {csv_path}")
        sys.exit(1)
        
    engine = get_db_connection()
    
    # 2. Verificar existencia de tabla en BD
    try:
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            print(f"Error: La tabla '{table_name}' no existe en la base de datos.")
            sys.exit(1)
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        sys.exit(1)

    try:
        # 3. Leer CSV
        print(f"Leyendo archivo: {csv_path}")
        df = pd.read_csv(csv_path)
        
        if df.empty:
            print("Error: El archivo CSV está vacío.")
            sys.exit(1)
            
        # 4. Seleccionar los top N registros
        # Tomamos los primeros N registros del archivo (asumiendo que es el backup reciente de los últimos N registros)
        # Esto reinsertará los registros que se eliminaron (si el orden en el CSV se mantiene como salió del backup)
        df_to_insert = df.head(num_rows)
        
        if len(df_to_insert) < num_rows:
            print(f"Advertencia: Se solicitaron {num_rows} registros, pero el archivo solo contiene {len(df_to_insert)}.")
            
        # 5. Mostrar rango de confirmación
        if ref_col in df_to_insert.columns:
            min_id = df_to_insert[ref_col].min()
            max_id = df_to_insert[ref_col].max()
            print(f"--- CONFIRMACIÓN DE INSERCIÓN ---")
            print(f"Tabla: {table_name}")
            print(f"Registros a insertar: {len(df_to_insert)}")
            print(f"Rango de {ref_col}: {min_id} - {max_id}")
        else:
            print(f"Advertencia: La columna '{ref_col}' no existe en el CSV. No se puede mostrar el rango.")
            print(f"Registros a insertar: {len(df_to_insert)}")

        confirm = input("¿Está seguro de que desea continuar con la inserción? (s/n): ").strip().lower()
        if confirm != 's':
            print("Operación cancelada por el usuario.")
            sys.exit(0)

        # 6. Insertar en base de datos
        print("Insertando registros...")
        # if_exists='append' agrega a la tabla existente
        df_to_insert.to_sql(table_name, engine, if_exists='append', index=False)
        print("Inserción completada exitosamente.")

    except Exception as e:
        print(f"Error durante el proceso de inserción: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
