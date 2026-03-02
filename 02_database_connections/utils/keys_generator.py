"""
Generador de claves (PK/FK) basado en análisis de archivos CSV.
Analiza la estructura de los archivos en data/db_input y genera keys.json.
"""
import json
from pathlib import Path
import pandas as pd
import sys

# Define rutas base relativas a este script
# keys_generator.py está en 02_database_connections/utils/
# Necesitamos subir 3 niveles para llegar a la raíz: utils -> 02_database_connections -> root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / 'data' / 'db_input'
OUTPUT_FILE = Path(__file__).resolve().parent / 'keys.json'

def get_csv_headers(file_path):
    """Lee solo la cabecera (primera fila) de un archivo CSV."""
    try:
        # Lee solo 0 filas para obtener encabezados
        df = pd.read_csv(file_path, nrows=0)
        return df.columns.tolist()
    except Exception as e:
        print(f"Error leyendo {file_path}: {e}")
        return []

def generate_keys():
    """Genera el archivo de metadatos de claves escaneando los CSVs."""
    print(f"Escaneando archivos CSV en: {DATA_PATH}")
    
    # 1. Descubrimiento: Encuentra todos los archivos CSV recursivamente
    if not DATA_PATH.exists():
        print(f"Error: DATA PATH no existe: {DATA_PATH}")
        return []
        
    all_files = list(DATA_PATH.rglob('*.csv'))
    print(f"Se encontraron {len(all_files)} archivos CSV.")

    tables_metadata = []
    known_dim_pks = set()

    # 2. Identifica tablas y PK de dimensiones
    for f in all_files:
        table_name = f.stem
        is_dim = table_name.startswith('dim_')
        columns = get_csv_headers(f)
        
        pk = []
        
        # Regla para Dimensiones: PK contiene "ID"
        if is_dim:
            pk = [col for col in columns if "ID" in col]
            # Agregar al conjunto conocido para coincidencia de FK más tardecol]
            known_dim_pks.update(pk)
        
        # Regla para tablas de transacciones: PK contiene "SK" e "ID"
        else:
            pk = [col for col in columns if "SK" in col and "ID" in col]

        tables_metadata.append({
            'name': table_name,
            'is_dim': is_dim,
            'columns': columns,
            'pk': pk,
            'fk': []
        })

    # 3. Identifica FKs en tablas principales basándose en PKs de dimensiones
    # Logica FK: "La primary key creada va a ser la foreign key en las tablas de transacciones"
    
    final_output = []

    for table in tables_metadata:
        # FK logic: "La primary key creada va a ser la foreign key en las tablas de transacciones"
        
        if not table['is_dim']:
            # Para cada tabla principal, buscamos columnas que coincidan con los PKs de las dimensiones conocidas.
            # Esto es una heurística simple: si una columna en la tabla principal coincide con un PK de dimensión, la consideramos FK.            
            fks = [col for col in table['columns'] if col in known_dim_pks and col not in table['pk']]
            table['fk'] = fks
        
        # Construccion de objeto final para exportar
        final_output.append({
            "table_name": table['name'],
            "pk": table['pk'],
            "fk": table['fk']
        })

    return final_output

if __name__ == "__main__":
    keys_data = generate_keys()
    
    # Exportacion a JSON
    try:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(keys_data, f, indent=4)
        print(f"Claves exportadas correctamente en: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error escribiendo archivo de salida: {e}")
