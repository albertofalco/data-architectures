"""Export the latest configured MySQL table rows to backup CSV files."""

# ==================== IMPORTS ====================

import sys
import os
import yaml
import pandas as pd
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv
from pathlib import Path

# ==================== CONFIGURATION ====================

# Project paths.
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
ASSETS_DIR = CURRENT_DIR.parent / "assets"
ENV_PATH = PROJECT_ROOT / ".env"
CONFIG_PATH = CURRENT_DIR / "config.yml"

# Load environment variables.
if not ENV_PATH.exists():
    print(f"Error: No se encontró el archivo .env en {ENV_PATH}")
    sys.exit(1)
load_dotenv(ENV_PATH)

# Load backup configuration from YAML.
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

# ==================== HELPER FUNCTIONS ====================

def get_db_connection():
    """Create and return a SQLAlchemy engine for the configured MySQL database."""
    try:
        host = os.getenv("DB_HOST")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        dbname = os.getenv("DB_NAME")
        
        if not all([host, user, dbname]):
             print("Error: Faltan variables de entorno para la conexión a BD.")
             sys.exit(1)

        # Use the mysql-connector-python driver.
        connection_url = f"mysql+mysqlconnector://{user}:{password}@{host}/{dbname}"
        print(f"\nConectando a la base de datos: {dbname}...\n")
        engine = create_engine(connection_url)
        return engine
    except Exception as e:
        print(f"Error al configurar la conexión: {e}")
        sys.exit(1)

# ==================== MAIN FUNCTIONS ====================

def main():
    """Export the latest configured rows from each table to CSV."""
    engine = get_db_connection()
    
    # Verify the database connection.
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        sys.exit(1)

    # Create the backup directory when needed.
    if not ASSETS_DIR.exists():
        print(f"Creando directorio de assets: {ASSETS_DIR}")
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for table_name, limit, order_col in TARGET_TABLES:
        print(f"Procesando backup para: {table_name}")
        
        if table_name not in existing_tables:
            print(f"Error: La tabla '{table_name}' no existe en la base de datos.")
            sys.exit(1)
            
        try:
            # Fetch the latest rows, then restore ascending order in the CSV.
            query = f"SELECT * FROM {table_name} ORDER BY {order_col} DESC LIMIT {limit}"
            df = pd.read_sql(query, engine)
            df = df.sort_values(by=order_col, ascending=True)
            
            if df.empty:
                print(f"Advertencia: No se encontraron registros para la tabla {table_name}.")
                sys.exit(1)
                
            # Report incomplete backup batches.
            if len(df) < limit:
                print(f"Advertencia: Se solicitaron {limit} registros, pero solo se encontraron {len(df)}.")

            # Write the backup CSV.
            output_file = ASSETS_DIR / f"{table_name}.csv"
            df.to_csv(output_file, index=False)
            
            # Report the exported identifier range.
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

# ==================== EXECUTION ====================

if __name__ == "__main__":
    main()
