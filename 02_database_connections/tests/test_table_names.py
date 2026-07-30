"""Compare MySQL table names with normalized CSV filenames."""

# ==================== IMPORTS ====================

import argparse, os
from getpass import getpass
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import mysql.connector

# ==================== CONFIGURATION ====================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')

# ==================== MAIN FUNCTIONS ====================

def main():
    """Compare database table names with normalized CSV filenames."""
    # Parse database connection arguments.
    parser = argparse.ArgumentParser(description="Cargador de CSV a MySQL")
    parser.add_argument("--host", default=os.getenv('DB_HOST', '127.0.0.1'), help="Host de la base de datos")
    parser.add_argument("--user", default=os.getenv('DB_USER', 'root'), help="Usuario")
    parser.add_argument("--password", action="store_true", help="Solicitar contraseña de forma interactiva")
    parser.add_argument("--database", default=os.getenv('DB_NAME', ''), help="Nombre de la base de datos")

    args = parser.parse_args()
    password = getpass("Password: ") if args.password else os.getenv('DB_PASSWORD', '')

    data_path = BASE_DIR / 'data' / 'db_input'

    try:
        # Connect to MySQL.
        conn = mysql.connector.connect(
            host=args.host,
            user=args.user,
            password=password,
        )
        cursor = conn.cursor()

        # Fetch database table names.
        cursor.execute(f"USE {args.database}")
        cursor.execute("SHOW TABLES")
        tablas_db = {tabla[0] for tabla in cursor.fetchall()}
        
        # Collect normalized CSV stems.
        archivos_en_carpeta = [f for f in Path(data_path).rglob('*.csv') if f.is_file()]
        nombres_csv = {f.stem.lower() for f in archivos_en_carpeta}
        
        # Compare both name sets.
        coincidencias = tablas_db.intersection(nombres_csv)
        solo_en_db = tablas_db - nombres_csv
        solo_en_carpeta = nombres_csv - tablas_db

        # Print the comparison summary.
        print("-" * 30)
        print(f"RESUMEN DE COMPARACIÓN")
        print("-" * 30)
        
        print(f"✅ Coincidencias ({len(coincidencias)}):")
        for item in sorted(coincidencias): print(f"  - {item}")

        print(f"\n⚠️ Tablas en DB sin archivo CSV ({len(solo_en_db)}):")
        for item in sorted(solo_en_db): print(f"  - {item}")

        print(f"\n📂 Archivos CSV sin tabla en DB ({len(solo_en_carpeta)}):")
        for item in sorted(solo_en_carpeta): print(f"  - {item}")

    except mysql.connector.Error as err:
        print(f"Error de base de datos: {err}")
    except FileNotFoundError:
        print(f"Error: No se encontró la carpeta '{data_path}'")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# ==================== EXECUTION ====================

if __name__ == "__main__":
    main()
