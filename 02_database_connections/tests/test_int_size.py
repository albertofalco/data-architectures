"""
Script para evaluar si las columnas de los archivos CSV requieren BigInteger.

Este script analiza cada archivo CSV en el directorio de entrada y verifica si
alguna columna numérica contiene valores que exceden el rango de un entero de 32 bits
(-2,147,483,648 a 2,147,483,647).

Las columnas identificadas se reportan como candidatas para usar BigInteger en la base de datos.
"""

# ============================================================================
# IMPORTACION DE LIBRERIAS
# ============================================================================

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACION DE VARIABLES
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')
DATA_PATH = BASE_DIR / 'data' / 'db_input'

# Límites de un entero de 32 bits (signed)
INT32_MIN = -2147483648
INT32_MAX = 2147483647

# ============================================================================
# FUNCIONES
# ============================================================================

def check_bigint_candidates(df, filename):
    """
    Analiza un DataFrame para identificar columnas que requieren BigInteger.
    """
    bigint_candidates = []
    
    # Iterar sobre las columnas numéricas
    # Usamos select_dtypes para incluir enteros y flotantes (por si hay nulos representados como float)
    numeric_cols = df.select_dtypes(include=['number']).columns
    
    for col in numeric_cols:
        # Obtener min y max ignorando nulos
        min_val = df[col].min()
        max_val = df[col].max()
        
        # Verificar si hay valores válidos (no todo NaN)
        if pd.isna(min_val) or pd.isna(max_val):
            continue

        # Verificar si excede los límites de 32 bits
        if min_val < INT32_MIN or max_val > INT32_MAX:
            bigint_candidates.append({
                'column': col,
                'min_value': min_val,
                'max_value': max_val,
                'type': str(df[col].dtype)
            })
            
    if bigint_candidates:
        print(f"\n⚠️  Archivo: {filename}")
        for candidate in bigint_candidates:
            print(f"   - Columna '{candidate['column']}' requiere BigInteger")
            print(f"     (Min: {candidate['min_value']}, Max: {candidate['max_value']}, Tipo actual: {candidate['type']})")
        return True
    
    return False

def analyze_csv_files(dir_path):
    """
    Recorre los archivos CSV en el directorio y los analiza.
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Error: La carpeta {dir_path} no existe.")

    archivos = list(dir_path.rglob('*.csv'))
    print(f"Encontrados {len(archivos)} archivos CSV para analizar.")
    
    files_with_bigint = 0
    
    for archivo in archivos:
        print(f"Analizando: {archivo.name}...", end='\r')
        try:
            # Lectura con dtype_backend="numpy_nullable" como solicitado
            # Esto permite enteros con nulos (Int64, etc.)
            df = pd.read_csv(archivo, dtype_backend="numpy_nullable")
            
            if check_bigint_candidates(df, archivo.name):
                files_with_bigint += 1
                
        except Exception as e:
            print(f"\n❌ Error al leer {archivo.name}: {e}")

    print(f"\n\nAnálisis completado.")
    if files_with_bigint > 0:
        print(f"Se encontraron {files_with_bigint} archivos con columnas candidatas a BigInteger.")
    else:
        print("✅ No se encontraron columnas que requieran BigInteger en los archivos analizados.")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("Iniciando análisis de tipos de datos (BigInteger)...")
    
    try:
        analyze_csv_files(DATA_PATH)
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
