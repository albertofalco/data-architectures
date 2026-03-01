"""
Script de creación de diccionarios en ClickHouse.

Este script genera diccionarios en ClickHouse basados en las tablas de dimensiones
disponibles en la base de datos de staging (MySQL).
"""
import clickhouse_connect
import yaml
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Detalles de conexión a ClickHouse
CH_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CH_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CH_USER = os.getenv("CLICKHOUSE_USER", "default")
CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")

# Detalles de conexión a MySQL (para fuente de diccionario)
MYSQL_HOST = os.getenv("MYSQL_HOST_FOR_CH", "host.docker.internal")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "mysql-clickhouse")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "data_arch_prod")

def load_config():
    """Carga la configuración desde el archivo YAML."""
    with open("03_dw_pipeline/src/config.yml", "r") as f:
        return yaml.safe_load(f)

def create_dictionaries():
    """
    Crea diccionarios en ClickHouse para cada tabla de dimensión encontrada.
    
    Consulta los metadatos de las tablas en staging y genera las sentencias
    CREATE DICTIONARY correspondientes.
    """
    config = load_config()
    staging_db = config["databases"]["staging_db"]
    storage_db = config["databases"]["storage_db"]

    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT, username=CH_USER, password=CH_PASSWORD)
    except Exception as e:
        print(f"Failed to connect to ClickHouse: {e}")
        return

    # Obtener tablas de dimensiones desde staging
    print(f"Fetching dimension tables from {staging_db}...")
    
    # Consultar system.columns para obtener definiciones de tablas desde la base de datos con motor MySQL
    query = f"""
    SELECT table, name, type
    FROM system.columns
    WHERE database = '{staging_db}' AND table LIKE 'dim_%'
    ORDER BY table, position
    """
    
    try:
        result = client.query(query)
        columns_data = result.result_rows
    except Exception as e:
        print(f"Error querying system.columns: {e}")
        return
    
    if not columns_data:
        print("No dimension tables found.")
        return

    tables = {}
    for row in columns_data:
        table_name = row[0]
        col_name = row[1]
        col_type = row[2]
        
        if table_name not in tables:
            tables[table_name] = []
        tables[table_name].append({'name': col_name, 'type': col_type})

    for table_name, columns in tables.items():
        # La primera columna es la PK
        pk_col = columns[0]['name']
        
        # Construir cadena de lista de columnas
        # Asegurar que el tipo es compatible o utilizar el criterio de ClickHouse
        col_list_str = ", ".join([f"{col['name']} {col['type']}" for col in columns])
        
        dict_name = f"dict_{table_name}"
        full_dict_name = f"{storage_db}.{dict_name}"
        
        print(f"Creating dictionary {full_dict_name}...")
        
        create_query = f"""
        CREATE DICTIONARY IF NOT EXISTS {full_dict_name}
        ({col_list_str})
        PRIMARY KEY {pk_col}
        SOURCE(MYSQL(
            HOST '{MYSQL_HOST}' 
            PORT {MYSQL_PORT}
            USER '{MYSQL_USER}' 
            PASSWORD '{MYSQL_PASSWORD}' 
            DB '{MYSQL_DB}' 
            TABLE '{table_name}'
        ))
        LIFETIME(MIN 3600 MAX 7200)
        LAYOUT(HASHED())
        """
        
        try:
            client.command(create_query)
            print(f"Dictionary {full_dict_name} created successfully.")
        except Exception as e:
            print(f"Error creating dictionary {full_dict_name}: {e}")

if __name__ == "__main__":
    create_dictionaries()
