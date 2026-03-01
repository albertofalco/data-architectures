"""
Script de prueba de conexión a ClickHouse.

Verifica que las credenciales y la conectividad con el servidor de ClickHouse
sean correctas y lista las bases de datos disponibles.
"""
import clickhouse_connect
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_connection():
    """
    Intenta conectar a ClickHouse y listar las bases de datos.
    """
    # Detalles de conexión a ClickHouse
    host = os.getenv("CLICKHOUSE_HOST", "localhost")
    try:
        port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    except ValueError:
        port = 8123
        
    user = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "")

    print(f"Connecting to ClickHouse at {host}:{port} as {user}...")

    try:
        client = clickhouse_connect.get_client(host=host, port=port, username=user, password=password)
        print("Connection successful!")
        
        print("\nDatabases:")
        result = client.query("SHOW DATABASES")
        for row in result.result_rows:
            print(f"- {row[0]}")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()