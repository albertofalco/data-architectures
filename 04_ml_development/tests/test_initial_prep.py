"""Structural and content parity checks for raw and Data Warehouse DataFrames."""

# ==================== IMPORTS ====================

import yaml
import os
import polars as pl
import pathlib
import zipfile

# ==================== CONFIGURATION ====================

FILE_PATH = pathlib.Path(__file__).resolve()
MODULE_DIR = pathlib.Path(FILE_PATH).parent.parent
BASE_DIR = MODULE_DIR.parent

with open(pathlib.Path(FILE_PATH).parent.parent / "config.yml", "r") as f:
    config = yaml.safe_load(f)

RAW_DATA_DIR = pathlib.Path(BASE_DIR) / config["paths"]["raw_data"]
DW_DATA_DIR = pathlib.Path(BASE_DIR) / config["paths"]["dw_data"]

TABLES_LIST = config.get("tables", {})

# ==================== HELPER FUNCTIONS ====================

def read_dataframes(dw_file_path, raw_file_path) -> tuple[pl.DataFrame, pl.DataFrame] | None:
    """Read the Data Warehouse parquet and matching raw CSV DataFrames."""
    try: 
        df_dw = pl.read_parquet(dw_file_path)
        df_raw = pl.read_csv(raw_file_path)       

        return df_dw, df_raw

    except Exception as e:
        print(f"Error reading dataframes: {e}")
        return None

def apply_schema_to_matching_columns(source_df: pl.DataFrame, target_df: pl.DataFrame) -> pl.DataFrame:
    """Apply source data types to columns shared with the target DataFrame."""
    modified_df = target_df.clone()
    source_schema = source_df.schema

    common_columns = [col for col in source_schema if col in modified_df.columns]

    for col_name in common_columns:
        source_dtype = source_schema[col_name]
        current_dtype = modified_df.schema[col_name]

        if current_dtype != source_dtype:
            modified_df = modified_df.with_columns(pl.col(col_name).cast(source_dtype))
    return modified_df

def apply_preprocessing(df, name, row_slice=None, exclude_cols=None, sort_cols=None):
    """Apply configured column exclusion, sorting, and row slicing."""
    if exclude_cols:
        df = df.drop(exclude_cols)
        print(f"[{name}] Columnas excluidas: {exclude_cols}")

    if sort_cols:
        try:
            df = df.sort(sort_cols)
            print(f"[{name}] Ordenado por: {sort_cols}")
        except Exception as e:
            print(f"Advertencia: No se pudo ordenar {name}. Error: {e}")
            
    if row_slice:
        try:
            start, end = map(int, row_slice.split(':'))
            df = df.slice(start, end - start)
            print(f"[{name}] Aplicado slice: {row_slice}")
        except ValueError:
            print(f"Error: Formato de slice inválido para {name}: '{row_slice}'")
            
    return df

def check_structure(df1, df2, n1, n2):
    """Compare DataFrame dimensions and column names."""
    print(f"\n--- Estructura ---")
    print(f"Shape: {n1}={df1.shape}, {n2}={df2.shape}")
    
    cols1, cols2 = set(df1.columns), set(df2.columns)
    common = cols1.intersection(cols2)
    only_df1 = cols1 - cols2
    only_df2 = cols2 - cols1
    
    print(f"Columnas comunes: {len(common)}")
    if only_df1: print(f"Únicas en {n1}: {only_df1}")
    if only_df2: print(f"Únicas en {n2}: {only_df2}")
    
    return list(common), len(only_df1) == 0 and len(only_df2) == 0

def check_dtypes(df1, df2, common_cols):
    """Return data type mismatches for columns shared by both DataFrames."""
    mismatches = []
    for col in sorted(common_cols):
        t1, t2 = df1.schema[col], df2.schema[col]
        if t1 != t2:
            mismatches.append((col, t1, t2))
    
    if mismatches:
        print("\n--- Diferencias de Tipos ---")
        for col, t1, t2 in mismatches:
            print(f"  - {col}: {t1} vs {t2}")
    return mismatches

def compare_content(df1, df2, common_cols, float_tolerance):
    """Compare shared columns row by row with numeric tolerance."""
    print(f"\n--- Contenido (Tolerancia: {float_tolerance}) ---")
    mismatched_report = []

    for col in sorted(common_cols):
        c1, c2 = df1[col], df2[col]
        dtype = df1.schema[col]
        
        # Null mismatches apply independently of the column data type.
        null_diff = c1.is_null() != c2.is_null()
        
        if dtype in [pl.Float32, pl.Float64]:
            val_diff = (c1.is_not_null() & c2.is_not_null()) & ((c1 - c2).abs() > float_tolerance)
        else:
            val_diff = (c1.is_not_null() & c2.is_not_null()) & (c1 != c2)

        total_mismatches = (null_diff | val_diff).sum()
        if total_mismatches > 0:
            mismatched_report.append((col, total_mismatches))

            df1_filtered = df1.filter(null_diff | val_diff).select([pl.col("*"), pl.lit(col).alias("_DIFF_COLUMN")])
            df2_filtered = df2.filter(null_diff | val_diff).select([pl.col("*"), pl.lit(col).alias("_DIFF_COLUMN")])
            
            df1_filtered = df1_filtered.with_columns([
                pl.lit("df1").alias("_SOURCE")
            ])
            df2_filtered = df2_filtered.with_columns([
                pl.lit("df2").alias("_SOURCE")
            ])

            report_df = df1_filtered.join(df2_filtered, on=[c for c in df1_filtered.columns if c not in ["_SOURCE", "_DIFF_COLUMN"]], how="outer")
            
            report_path = pathlib.Path(__file__).parent / f"diff_{col}.csv"
            report_df.write_csv(report_path)
            print(f"  - {col}: {total_mismatches} diferencias -> exportado a {report_path.name}")

    if not mismatched_report:
        print("Contenidos idénticos en columnas comunes")

def compare_polars_dataframes(df1, df2, **kwargs):
    """Run preprocessing and parity checks for two Polars DataFrames."""
    n1 = kwargs.get("df1_name", "df1")
    n2 = kwargs.get("df2_name", "df2")
    tol = kwargs.get("float_tolerance", 1e-5)

    df1_proc = apply_preprocessing(df1, n1, kwargs.get("df1_row_slice"), 
                                   kwargs.get("df1_exclude_cols"), kwargs.get("df1_col_sort"))
    df2_proc = apply_preprocessing(df2, n2, kwargs.get("df2_row_slice"), 
                                   kwargs.get("df2_exclude_cols"), kwargs.get("df2_col_sort"))

    common_cols, same_cols = check_structure(df1_proc, df2_proc, n1, n2)
    dtype_mismatches = check_dtypes(df1_proc, df2_proc, common_cols)

    print(f"\n--- Nulos ---")
    print(f"Nulos en {n1}: {df1_proc.null_count().sum_horizontal().item()}")
    print(f"Nulos en {n2}: {df2_proc.null_count().sum_horizontal().item()}")

    if df1_proc.shape == df2_proc.shape and not dtype_mismatches and same_cols:
        compare_content(df1_proc, df2_proc, common_cols, tol)
    else:
        print("\n[!] Comparación de contenido omitida: Los DFs no son estructuralmente idénticos.")

    return df1_proc, df2_proc


# ==================== MAIN FUNCTIONS ====================

def df_walker(tables_list, dw_data_dir, raw_data_dir, dw_pattern="*.parquet", raw_pattern="*.csv"):
    """Find configured raw and DW tables and run their comparisons."""
    if type(dw_data_dir) is not pathlib.PosixPath:
        dw_data_dir = pathlib.Path(dw_data_dir)
    if type(raw_data_dir) is not pathlib.PosixPath:
        raw_data_dir = pathlib.Path(raw_data_dir)

    for table in tables_list:
        dw_tbl_name = f"rep_{table.lower()}{dw_pattern.replace('*', '')}"
        raw_tbl_name = f"{table}{raw_pattern.replace('*', '')}"
        for dw_file_path in dw_data_dir.rglob(dw_pattern):
            if dw_tbl_name in dw_file_path.name:
                for raw_file_path in raw_data_dir.rglob(raw_pattern):
                    if raw_tbl_name in raw_file_path.name:
                        
                        df_result = read_dataframes(dw_file_path=dw_file_path, raw_file_path=raw_file_path)
                        
                        if df_result is None:
                            print(f"[ERROR] No se pudieron leer los datos para {table}")
                            continue
                        
                        df_dw, df_raw = df_result

                        df_raw = apply_schema_to_matching_columns(source_df=df_dw, target_df=df_raw)

                        print(f"\n=== Procesando tabla: {table} ===")
                        
                        a, b = compare_polars_dataframes(df_dw, 
                                                  df_raw, 
                                                  df1_name=f"df_{dw_file_path.stem}", 
                                                  df2_name=f"df_{raw_file_path.stem}",
                                                  float_tolerance=0.01,
                                                  df1_row_slice=tables_list[table]["dw_row_slice"] if 'dw_row_slice' in tables_list[table] else None,
                                                  df2_row_slice=tables_list[table]["raw_row_slice"] if 'raw_row_slice' in tables_list[table] else None,
                                                  df1_exclude_cols=tables_list[table]['dw_exclude_col'] if 'dw_exclude_col' in tables_list[table] else None,
                                                  df2_exclude_cols=tables_list[table]['raw_exclude_col'] if 'raw_exclude_col' in tables_list[table] else None,
                                                  df1_col_sort=tables_list[table]['dw_sort_col'] if 'dw_sort_col' in tables_list[table] else None,
                                                  df2_col_sort=tables_list[table]['raw_sort_col'] if 'raw_sort_col' in tables_list[table] else None
                                                  )

# ==================== EXECUTION ====================

if __name__ == "__main__":
    df_walker(TABLES_LIST, DW_DATA_DIR, RAW_DATA_DIR, dw_pattern="*.parquet", raw_pattern="*.csv")
