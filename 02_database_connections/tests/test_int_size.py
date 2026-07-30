"""Identify normalized CSV columns that require MySQL BIGINT storage."""

# ==================== IMPORTS ====================

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

# ==================== CONFIGURATION ====================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')
DATA_PATH = BASE_DIR / 'data' / 'db_input'

# Signed 32-bit integer bounds.
INT32_MIN = -2147483648
INT32_MAX = 2147483647

# ==================== HELPER FUNCTIONS ====================

def check_bigint_candidates(df, filename):
    """Return whether a DataFrame contains values requiring BIGINT."""
    bigint_candidates = []
    
    # Include floating-point columns because nullable integers may be inferred as floats.
    numeric_cols = df.select_dtypes(include=['number']).columns
    
    for col in numeric_cols:
        # Compute bounds while ignoring null values.
        min_val = df[col].min()
        max_val = df[col].max()
        
        # Skip columns without valid numeric values.
        if pd.isna(min_val) or pd.isna(max_val):
            continue

        # Record values outside the signed 32-bit range.
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
    """Analyze CSV files recursively for BIGINT candidates."""
    if not dir_path.exists():
        raise FileNotFoundError(f"Error: La carpeta {dir_path} no existe.")

    archivos = list(dir_path.rglob('*.csv'))
    print(f"Encontrados {len(archivos)} archivos CSV para analizar.")
    
    files_with_bigint = 0
    
    for archivo in archivos:
        print(f"Analizando: {archivo.name}...", end='\r')
        try:
            # Preserve nullable integer types while reading.
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

# ==================== MAIN FUNCTIONS ====================

def main():
    """Run BIGINT candidate analysis for normalized CSV files."""
    print("Iniciando análisis de tipos de datos (BigInteger)...")
    
    try:
        analyze_csv_files(DATA_PATH)
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        sys.exit(1)

# ==================== EXECUTION ====================

if __name__ == '__main__':
    main()
