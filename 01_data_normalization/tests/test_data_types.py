"""Report inferred data types for columns in normalized CSV files."""

# ==================== IMPORTS ====================

from pathlib import Path
import pandas as pd
import csv
import sys

# ==================== CONFIGURATION ====================

# Project and output paths.
script_dir = Path(__file__).parent.resolve()

data_dir = script_dir.parent.parent / "data" / "db_input"

output_file = script_dir / "data_types.csv"

# ==================== EXECUTION ====================

# Require the normalized data directory.
if not data_dir.exists():
    print(f"ERROR: No se encontro el directorio: {data_dir}")
    sys.exit(1)

# Write one report row per CSV column.
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    # Keep the established Spanish report column names for compatibility.
    writer.writerow(["nombre_subcarpeta", "nombre_archivo", "columna", "tipo", "flag_id_no_int64"])

    # Scan normalized dataset directories.
    for subdir in sorted(data_dir.iterdir(), key=lambda x: x.name.lower()):
        if subdir.is_dir():
            # Analyze every CSV in the dataset directory.
            for csv_path in sorted(subdir.glob("*.csv"), key=lambda x: x.name.lower()):
                print(f"Leyendo {csv_path.name}...")
                
                # Sample rows and preserve nullable integer types.
                df = pd.read_csv(csv_path, nrows=10000, dtype_backend='numpy_nullable')
                
                # Record the inferred type for each column.
                for col, dtype in df.dtypes.items():
                    dtype_str = str(dtype)
                    # Flag identifier columns that are not 64-bit integers.
                    flag = 1 if "ID" in col and dtype_str not in ("int64", "Int64") else 0
                    writer.writerow([subdir.name, csv_path.name, col, dtype_str, flag])

print(f"CSV generado: {output_file}")
sys.exit(0)
