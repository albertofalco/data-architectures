"""
Test Data Types - Análisis de tipos de datos de archivos CSV

Script que analiza los archivos CSV en el directorio de datos de entrada,
extrae los tipos de datos de cada columna y genera un archivo CSV con el resultado.
También marca con un flag las columnas que contienen 'ID' pero no son de tipo int64.
"""

from pathlib import Path
import pandas as pd
import csv
import sys

# Directorio donde se encuentra este script
script_dir = Path(__file__).parent.resolve()

# Directorio donde estan los datos de entrada
data_dir = script_dir.parent.parent / "data" / "db_input"

# Archivo de salida con el analisis de tipos de datos
output_file = script_dir / "data_types.csv"

# Verificar que el directorio de datos existe
if not data_dir.exists():
    print(f"ERROR: No se encontro el directorio: {data_dir}")
    sys.exit(1)

# Abrir archivo de salida y escribir header
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    # Columnas del archivo de salida:
    # - nombre_subcarpeta: carpeta que contiene el archivo CSV
    # - nombre_archivo: nombre del archivo CSV
    # - columna: nombre de la columna
    # - tipo: tipo de datos de la columna (pandas)
    # - flag_id_no_int64: 1 si la columna tiene 'ID' en el nombre pero no es int64
    writer.writerow(["nombre_subcarpeta", "nombre_archivo", "columna", "tipo", "flag_id_no_int64"])

    # Recorrer cada subdirectorio en el directorio de datos
    for subdir in sorted(data_dir.iterdir(), key=lambda x: x.name.lower()):
        if subdir.is_dir():
            # Recorrer cada archivo CSV en el subdirectorio
            for csv_path in sorted(subdir.glob("*.csv"), key=lambda x: x.name.lower()):
                print(f"Leyendo {csv_path.name}...")
                
                # Leer solo las primeras 10000 filas para mejor rendimiento
                # dtype_backend='numpy_nullable' evita que las columnas con enteros y NaN
                # se conviertan a float64, usando Int64 en su lugar
                df = pd.read_csv(csv_path, nrows=10000, dtype_backend='numpy_nullable')
                
                # Analizar cada columna del DataFrame
                for col, dtype in df.dtypes.items():
                    dtype_str = str(dtype)
                    # Marcar columnas ID que no son int64/Int64 (potenciales problemas de tipo)
                    flag = 1 if "ID" in col and dtype_str not in ("int64", "Int64") else 0
                    writer.writerow([subdir.name, csv_path.name, col, dtype_str, flag])

print(f"CSV generado: {output_file}")
sys.exit(0)
