-- Purpose: Report MySQL table, column, constraint, and index metadata for the configured schemas.

-- Sections 1-4 inspect data_arch_prod; section 5 compares column and index metadata in data_arch_test.

-- ==================== 1. TABLE SUMMARY ====================

-- Summarize base table row estimates and column counts.
SELECT
    table_name AS 'Tabla', 
    table_rows AS 'Cantidad de Registros', 
    (SELECT COUNT(*) 
     FROM information_schema.columns 
     WHERE table_schema = t.table_schema 
       AND table_name = t.table_name) AS 'Cantidad de Columnas'
FROM 
    information_schema.tables t
WHERE 
    table_schema = 'data_arch_prod' 
    AND table_type = 'BASE TABLE';

-- ==================== 2. COLUMN DETAILS ====================

-- Report column types, nullability, key indicators, and defaults.

SELECT 
    c.table_name AS 'Tabla', 
    c.column_name AS 'Columna', 
    c.column_type AS 'Tipo de Dato', 
    c.is_nullable AS 'Es Nullable',
    CASE WHEN c.column_key = 'PRI' THEN 'SÍ' ELSE 'NO' END AS 'Es PK',
    CASE WHEN c.column_key = 'MUL' THEN 'SÍ' ELSE 'NO' END AS 'Es FK/Índice',
    c.column_default AS 'Valor por Defecto'
FROM 
    information_schema.columns c
WHERE 
    c.table_schema = 'data_arch_prod'
ORDER BY 
    c.table_name, c.ordinal_position;

-- ==================== 3. FOREIGN KEY ANALYSIS ====================

-- Relate column metadata to key usage by schema, table, and column.
SELECT 
    c.TABLE_NAME AS 'Tabla', 
    c.COLUMN_NAME AS 'Columna', 
    c.COLUMN_TYPE AS 'Tipo de Dato', 
    c.IS_NULLABLE AS 'Permite Nulos',
    CASE 
        WHEN c.COLUMN_KEY = 'PRI' THEN 'PRIMARY KEY'
        WHEN k.REFERENCED_TABLE_NAME IS NOT NULL THEN 'FOREIGN KEY'
        WHEN c.COLUMN_KEY = 'UNI' THEN 'UNIQUE INDEX'
        WHEN c.COLUMN_KEY = 'MUL' THEN 'INDEX (Non-Unique)'
        ELSE 'NONE'
    END AS 'Tipo de Restricción',
    k.REFERENCED_TABLE_NAME AS 'Tabla Referenciada',
    k.REFERENCED_COLUMN_NAME AS 'Columna Referenciada'
FROM 
    information_schema.COLUMNS c
LEFT JOIN 
    information_schema.KEY_COLUMN_USAGE k 
    ON c.TABLE_SCHEMA = k.TABLE_SCHEMA 
    AND c.TABLE_NAME = k.TABLE_NAME 
    AND c.COLUMN_NAME = k.COLUMN_NAME
WHERE 
    c.TABLE_SCHEMA = 'data_arch_prod'
ORDER BY 
    c.TABLE_NAME, c.ORDINAL_POSITION;

-- ==================== 4. COLUMN ATTRIBUTES ====================

-- Inspect detailed column attributes in the production schema.

USE data_arch_prod;
SELECT 
    TABLE_NAME AS 'Tabla',
    COLUMN_NAME AS 'Columna',
    ORDINAL_POSITION AS 'Posición',
    COLUMN_TYPE AS 'Tipo Detallado',
    IS_NULLABLE AS 'Nulable',
    COLUMN_KEY AS 'Llave',           -- PRI is primary, UNI is unique, and MUL is indexed.
    EXTRA AS 'Extra'
FROM 
    INFORMATION_SCHEMA.COLUMNS
WHERE 
    TABLE_SCHEMA = 'data_arch_prod'
ORDER BY 
    TABLE_NAME,
    ORDINAL_POSITION;


-- ==================== 5. COLUMN AND INDEX INVENTORY ====================

-- Relate test-schema columns to index membership by schema, table, and column.
USE data_arch_test;
SELECT 
    c.TABLE_NAME AS 'Tabla',
    c.COLUMN_NAME AS 'Columna',
    c.ORDINAL_POSITION AS 'Posición',
    c.COLUMN_TYPE AS 'Tipo Detallado',
    c.IS_NULLABLE AS 'Nulable',
    c.COLUMN_KEY AS 'Llave',           -- PRI is primary, UNI is unique, and MUL is indexed.
    c.EXTRA AS 'Extra',
    s.INDEX_NAME AS 'Indice',
    s.SEQ_IN_INDEX AS 'Orden en Indice',
    s.NON_UNIQUE AS 'Es Único'         -- 0 is unique; 1 is non-unique.
FROM 
    INFORMATION_SCHEMA.COLUMNS c
LEFT JOIN 
    INFORMATION_SCHEMA.STATISTICS s
    ON c.TABLE_SCHEMA = s.TABLE_SCHEMA
   AND c.TABLE_NAME = s.TABLE_NAME
   AND c.COLUMN_NAME = s.COLUMN_NAME
WHERE 
    c.TABLE_SCHEMA = 'data_arch_test'
ORDER BY 
    c.TABLE_NAME, 
    c.ORDINAL_POSITION, 
    s.INDEX_NAME, 
    s.SEQ_IN_INDEX;
