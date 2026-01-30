#######################################################
# Script para cargar archivos CSV en una base de datos MySQL.
#######################################################

# Importacion de librerias.
import argparse, os
import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import errorcode
from pathlib import Path
from dotenv import load_dotenv

#######################################################
# CONFIGURACION
#######################################################

# Obtener la carpeta actual del script
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Cargar variables de entorno desde .env
load_dotenv(BASE_DIR / '.env')

# Rutas de datos
DATA_PATH = BASE_DIR / 'data' / 'db_input'

######################################################
# FUNCIONES PRINCIPALES
######################################################

def main():
    # 1. Configuración de argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Cargador de CSV a MySQL")
    parser.add_argument("--host", default=os.getenv('DB_HOST', '127.0.0.1'), help="Host de la base de datos")
    parser.add_argument("--user", default=os.getenv('DB_USER', 'root'), help="Usuario")
    parser.add_argument("--password", default=os.getenv('DB_PASSWORD', ''), help="Contraseña")
    parser.add_argument("--database", default=os.getenv('DB_NAME', ''), help="Nombre de la base de datos")
    
    args = parser.parse_args()
    
    # # 2. Conexión inicial (para verificar/crear la base de datos)
    try:
        conn = mysql.connector.connect(
            host=args.host,
            # port=3306,
            user=args.user,
            password=args.password,
            allow_local_infile = True # CRUCIAL: Habilitar la carga local de archivos
        )
        cursor = conn.cursor()
        
        # Verificar o crear la base de datos
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {args.database}")
        cursor.execute(f"USE {args.database}")
        print(f"Base de datos '{args.database}' lista.")

    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        return

    # 3. Procesar archivos CSV en la carpeta 'data'
    # Definir la ruta de datos.
    data_path = DATA_PATH
 
    if not os.path.exists(data_path):
        print(f"Error: La carpeta {data_path} no existe.")
        return

    archivos = [f for f in Path(data_path).rglob('*.csv') if f.is_file()]

    for archivo in archivos:
        nombre_archivo = archivo.name
        if nombre_archivo.endswith('.csv'):            
            nombre_tabla = archivo.stem.lower()
                        
            print(f"Procesando {nombre_archivo}...")
            
            try:
                # Leer CSV con Pandas
                df = pd.read_csv(archivo)  # (ruta_csv)
                df = df.replace({np.nan: None}) # Reemplaza valores NaN para compatibilidad con MYSQL.

                # Crear tabla si no existe (basado en las columnas del DataFrame)
                columnas = []
                for col_name, dtype in df.dtypes.items():
                    sql_type = "TEXT"
                    if "int" in str(dtype): sql_type = "INT"
                    elif "float" in str(dtype): sql_type = "FLOAT"
                    columnas.append(f"`{col_name}` {sql_type}")
                crear_tabla_sql = f"CREATE TABLE IF NOT EXISTS `{nombre_tabla}` ({', '.join(columnas)})"
                cursor.execute(crear_tabla_sql)
                
                # Limpiar tabla antes de cargar (Opcional, según tu necesidad)
                cursor.execute(f"TRUNCATE TABLE `{nombre_tabla}`")

                # SQL para la carga masiva
                query = f"""
                LOAD DATA LOCAL INFILE '{str(archivo)}'
                INTO TABLE {nombre_tabla}
                FIELDS TERMINATED BY ',' 
                ENCLOSED BY '"'
                LINES TERMINATED BY '\\n'
                IGNORE 1 LINES; 
                """
                # (Nota: IGNORE 1 LINES se usa si tu CSV tiene encabezados)
                
                # Ejecucion de la query.
                cursor.execute(query)
                conn.commit()
                print(f"Tabla '{nombre_tabla}' cargada exitosamente.")

            except Exception as e:
                print(f"Error procesando {nombre_archivo}: {e}")
    
    print("Proceso completado.")

    # Cierre del cursor y conexion.
    if conn.is_connected():
        cursor.close()
        conn.close()

######################################################

if __name__ == '__main__':
    main()
