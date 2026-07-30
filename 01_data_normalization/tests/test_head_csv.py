"""Print HOUSETYPE_MODE_ID values from the normalized application_train CSV."""

# ==================== IMPORTS ====================

from pathlib import Path
import pandas as pd
import csv
import sys

# ==================== CONFIGURATION ====================

# Project and input paths.
script_dir = Path(__file__).parent.resolve()

data_dir = script_dir.parent.parent / "data" / "db_input"

# ==================== EXECUTION ====================

# Require the normalized application_train CSV.
csv_path = data_dir / "application_train" / "application_train.csv"
if not csv_path.exists():
    print(f"ERROR: No se encontro el archivo: {csv_path}")
    sys.exit(1)

print(f"Leyendo archivo: {csv_path}")
print("-" * 50)

with open(csv_path, "r", newline="\n", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        if count < 20:
            print(f"Fila {count + 1}: {row['HOUSETYPE_MODE_ID']}")
            count += 1
        else:
            break

print("-" * 50)
print(f"Total de filas leidas: {count}")
