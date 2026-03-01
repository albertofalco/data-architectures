"""
Script de creación de bases de datos en ClickHouse.

Este script se encarga de verificar y crear las bases de datos necesarias
(staging y storage) en el servidor ClickHouse.
"""
import clickhouse_connect
import yaml
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Detalles de conexión a ClickHouse
CH_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CH_PORT = os.getenv("CLICKHOUSE_PORT", "8123")
CH_USER = os.getenv("CLICKHOUSE_USER", "default")
CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")

# Detalles de conexión a MySQL (para motor MySQL de ClickHouse)
MYSQL_HOST = os.getenv("MYSQL_HOST_FOR_CH", "host.docker.internal")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "mysql-clickhouse")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "data_arch_prod")

def load_config():
    """Carga la configuración desde el archivo YAML."""
    with open("03_dw_pipeline/src/config.yml", "r") as f:
        return yaml.safe_load(f)

def create_databases():
    """
    Crea las bases de datos de staging y storage en ClickHouse si no existen.
    
    La base de datos de staging utiliza el motor MySQL para conectar
    directamente con la fuente de datos.
    """
    config = load_config()
    staging_db = config["databases"]["staging_db"]
    storage_db = config["databases"]["storage_db"]

    client = clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT, username=CH_USER, password=CH_PASSWORD)

    # Verificar y crear base de datos de Staging
    print(f"Checking database {staging_db}...")
    exists = client.command(f"EXISTS DATABASE {staging_db}")
    if exists:
        print(f"Database {staging_db} already exists.")
    else:
        print(f"Creating database {staging_db}...")
        # Crear base de datos con motor MySQL
        query = f"""
        CREATE DATABASE {staging_db}
        ENGINE = MySQL('{MYSQL_HOST}:{MYSQL_PORT}', '{MYSQL_DB}', '{MYSQL_USER}', '{MYSQL_PASSWORD}')
        """
        client.command(query)
        print(f"Database {staging_db} created.")

    # Verificar y crear base de datos de almacenamiento
    print(f"Checking database {storage_db}...")
    exists = client.command(f"EXISTS DATABASE {storage_db}")
    if exists:
        print(f"Database {storage_db} already exists.")
    else:
        print(f"Creating database {storage_db}...")
        client.command(f"CREATE DATABASE {storage_db}")
        print(f"Database {storage_db} created.")

if __name__ == "__main__":
    create_databases()
