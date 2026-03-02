"""
Script de inserción de datos en tablas transaccionales.

Este script transfiere datos desde la base de datos de staging (MySQL)
a las tablas transaccionales en ClickHouse, generando IDs sintéticos cuando es necesario.
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

def load_config():
    """Carga la configuración desde el archivo YAML."""
    # Intentar cargar primero desde la ruta raíz del proyecto
    config_path = "03_dw_pipeline/src/config.yml"
    if not os.path.exists(config_path):
        # Respaldo a ruta local si se ejecuta desde src
        config_path = "config.yml"
        
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def insert_transaction_tables():
    """
    Ejecuta la inserción de datos en las tablas transaccionales.
    
    Itera sobre las configuraciones de Opción A y B para realizar
    la transferencia de datos correspondiente.
    """
    config = load_config()
    staging_db = config["databases"]["staging_db"]
    storage_db = config["databases"]["storage_db"]

    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=CH_PORT, username=CH_USER, password=CH_PASSWORD)
    except Exception as e:
        print(f"Failed to connect to ClickHouse: {e}")
        return

    # Procesar Opción A
    # Opción A: Inserción directa para tablas con PK en fuente
    print("Processing Option A inserts...")
    if 'option_a' in config['transaction_tables']:
        for table_info in config['transaction_tables']['option_a']:
            table_name = table_info['name']
            print(f"Inserting into {table_name}...")
            
            insert_query = f"""
            INSERT INTO {storage_db}.{table_name}
            SELECT * FROM {staging_db}.{table_name}
            """
            try:
                client.command(insert_query)
                print(f"Successfully inserted data into {storage_db}.{table_name}")
            except Exception as e:
                print(f"Error inserting into {table_name}: {e}")

    # Procesar Opción B
    # Opción B: Inserción con número de fila generado para tablas sin PK
    print("Processing Option B inserts...")
    if 'option_b' in config['transaction_tables']:
        for table_info in config['transaction_tables']['option_b']:
            table_name = table_info['name']
            print(f"Inserting into {table_name}...")
            
            # Usar rowNumberInAllBlocks() para generar _DW_ID
            insert_query = f"""
            INSERT INTO {storage_db}.{table_name}
            SELECT rowNumberInAllBlocks(), *
            FROM {staging_db}.{table_name}
            """
            try:
                client.command(insert_query)
                print(f"Successfully inserted data into {storage_db}.{table_name}")
            except Exception as e:
                print(f"Error inserting into {table_name}: {e}")

if __name__ == "__main__":
    insert_transaction_tables()
