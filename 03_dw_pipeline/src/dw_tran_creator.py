"""
Script de creación de tablas transaccionales en ClickHouse.

Este script crea tablas en ClickHouse (Engine=MergeTree) replicando la estructura
de las tablas fuente en MySQL (Staging), gestionando claves primarias y
agregando columnas de identidad cuando es necesario.
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
    with open("03_dw_pipeline/src/config.yml", "r") as f:
        return yaml.safe_load(f)

def get_table_columns(client, database, table):
    """Obtiene columnas y tipos de la tabla desde system.columns."""
    query = f"""
    SELECT name, type
    FROM system.columns
    WHERE database = '{database}' AND table = '{table}'
    ORDER BY position
    """
    result = client.query(query)
    return [{'name': row[0], 'type': row[1]} for row in result.result_rows]

def create_transaction_tables():
    """
    Crea las tablas transaccionales (hechos) en la base de datos de almacenamiento.
    
    Maneja dos opciones definidas en la configuración:
    - Opción A: Tablas con PK definida.
    - Opción B: Tablas sin PK (se genera _DW_ID).
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
    # Opción A: Tablas con restricción de PRIMARY KEY creadas en la base de datos mysql.
    print("Processing Option A tables...")
    for table_info in config['transaction_tables']['option_a']:
        table_name = table_info['name']
        print(f"Creating table {table_name}...")
        
        columns = get_table_columns(client, staging_db, table_name)
        if not columns:
            print(f"Warning: Table {table_name} not found in {staging_db}. Skipping.")
            continue
            
        col_defs = ", ".join([f"{col['name']} {col['type']}" for col in columns])
        
        # Detectar claves primarias: todas las columnas que comienzan con 'SK_ID'
        pk_cols = [col['name'] for col in columns if col['name'].startswith('SK_ID')]
        
        if not pk_cols:
            # Alternativa: usar primera columna si no se encuentra SK_ID (aunque inesperado para Opción A)
            print(f"Warning: No 'SK_ID' columns found for {table_name}. Using first column as PK.")
            pk_col_str = columns[0]['name']
        else:
            pk_col_str = ", ".join(pk_cols)
        
        create_query = f"""
        CREATE TABLE IF NOT EXISTS {storage_db}.{table_name}
        ({col_defs})
        ENGINE = MergeTree()
        ORDER BY ({pk_col_str})
        SETTINGS allow_nullable_key = 1
        """
        try:
            client.command(create_query)
            print(f"Table {storage_db}.{table_name} created with PK: ({pk_col_str}).")
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")

    # Procesar Opción B
    # Opción B: Tablas sin restricción de PRIMARY KEY creadas en la base de datos mysql.
    print("Processing Option B tables...")
    for table_info in config['transaction_tables']['option_b']:
        table_name = table_info['name']
        print(f"Creating table {table_name}...")
        
        columns = get_table_columns(client, staging_db, table_name)
        if not columns:
            print(f"Warning: Table {table_name} not found in {staging_db}. Skipping.")
            continue
            
        col_defs = ", ".join([f"{col['name']} {col['type']}" for col in columns])
        
        # Agregar columna _DW_ID
        create_query = f"""
        CREATE TABLE IF NOT EXISTS {storage_db}.{table_name}
        (
            _DW_ID UInt64,
            {col_defs}
        )
        ENGINE = MergeTree()
        ORDER BY _DW_ID
        """
        try:
            client.command(create_query)
            print(f"Table {storage_db}.{table_name} created.")
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")

if __name__ == "__main__":
    create_transaction_tables()
