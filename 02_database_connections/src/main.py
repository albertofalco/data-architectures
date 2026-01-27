import argparse, os
import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import errorcode

def main():
    # 1. Configuración de argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Cargador de CSV a MySQL")
    parser.add_argument("--host", required=True, help="Host de la base de datos")
    parser.add_argument("--user", required=True, help="Usuario")
    parser.add_argument("--password", required=True, help="Contraseña")
    parser.add_argument("--database", required=True, help="Nombre de la base de datos")
    
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
    # Subimos un nivel desde 'src' para encontrar 'data'
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    if not os.path.exists(data_path):
        print(f"Error: La carpeta {data_path} no existe.")
        return

    for archivo in os.listdir(data_path):
        if archivo.endswith('.csv'):
            nombre_tabla = os.path.splitext(archivo)[0]
            ruta_csv = os.path.join(data_path, archivo)
            
            print(f"Procesando {archivo}...")
            
            try:
                # Leer CSV con Pandas
                df = pd.read_csv(ruta_csv)
                df = df.replace({np.nan: None}) # Reemplaza valores NaN para compatibilidad con MYSQL.

                # Crear motor de conexión para Pandas (SQLAlchemy es recomendado con Pandas 2.0+)
                # Pero usaremos una inserción simple para mysql-connector 9.5.0
                
                # Crear tabla si no existe (basado en el CSV)
                # NOTA: En un entorno de producción se recomienda SQLAlchemy para esta parte
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
                LOAD DATA LOCAL INFILE '{ruta_csv}'
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
                print(f"Error procesando {archivo}: {e}")
    
    # Cierre del cursor y conexion.
    if conn.is_connected():
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
