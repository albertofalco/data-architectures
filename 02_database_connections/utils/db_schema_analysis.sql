-- 1. Resumen de Tablas
-- Este query proporciona un resumen de las tablas en la base de datos, incluyendo el nombre de la tabla, la cantidad de registros y la cantidad de columnas.

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

-- 2. Detalle de Columnas (Tipos, Keys e Índices)
-- Este query proporciona un detalle de las columnas de cada tabla, incluyendo el tipo de dato, si es nullable, si es clave primaria o foránea, y el valor por defecto.

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

-- 3. Análisis de Claves Foráneas
-- Este query identifica las claves foráneas en la base de datos, mostrando la tabla y columna que las contiene, así como la tabla y columna a la que hacen referencia.
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

-- 4. Análisis de extras
-- Consulta las columnas de todas las tablas dentro del esquema especificado

USE data_arch_prod;
SELECT 
    TABLE_NAME AS 'Tabla',           -- Nombre de la tabla
    COLUMN_NAME AS 'Columna',        -- Nombre de la columna
    ORDINAL_POSITION AS 'Posición',  -- Orden de la columna dentro de la tabla
    COLUMN_TYPE AS 'Tipo Detallado', -- Tipo de dato con longitud/precisión (ej: varchar(255), int(11))
    IS_NULLABLE AS 'Nulable',        -- Indica si la columna permite valores NULL (YES/NO)
    COLUMN_KEY AS 'Llave',           -- Tipo de llave: PRI (Primaria), UNI (Única), MUL (Indexada)
    EXTRA AS 'Extra'                 -- Información adicional (ej: auto_increment)
FROM 
    INFORMATION_SCHEMA.COLUMNS       -- Vista del diccionario de datos con metainformación de columnas
WHERE 
    TABLE_SCHEMA = 'data_arch_prod'  -- Filtra solo las tablas de este esquema/base de datos
ORDER BY 
    TABLE_NAME,                      -- Ordena primero por nombre de tabla
    ORDINAL_POSITION;                -- Luego por posición de columna dentro de cada tabla


-- 5. Diccionario de columnas + índices
-- Consulta las columnas de todas las tablas dentro del esquema especificado, incluyendo información sobre índices (si la columna forma parte de un índice y el tipo de índice)
USE data_arch_test;
SELECT 
    c.TABLE_NAME AS 'Tabla',           -- Nombre de la tabla
    c.COLUMN_NAME AS 'Columna',        -- Nombre de la columna
    c.ORDINAL_POSITION AS 'Posición',  -- Orden de la columna dentro de la tabla
    c.COLUMN_TYPE AS 'Tipo Detallado', -- Tipo de dato con longitud/precisión
    c.IS_NULLABLE AS 'Nulable',        -- Permite NULL (YES/NO)
    c.COLUMN_KEY AS 'Llave',           -- PRI (Primaria), UNI (Única), MUL (Indexada)
    c.EXTRA AS 'Extra',                -- Info adicional (ej: auto_increment)
    s.INDEX_NAME AS 'Indice',          -- Nombre del índice
    s.SEQ_IN_INDEX AS 'Orden en Indice', -- Posición de la columna dentro del índice
    s.NON_UNIQUE AS 'Es Único'         -- 0 = Único, 1 = No único
FROM 
    INFORMATION_SCHEMA.COLUMNS c
LEFT JOIN 
    INFORMATION_SCHEMA.STATISTICS s
    ON c.TABLE_SCHEMA = s.TABLE_SCHEMA
   AND c.TABLE_NAME = s.TABLE_NAME
   AND c.COLUMN_NAME = s.COLUMN_NAME
WHERE 
    c.TABLE_SCHEMA = 'data_arch_test'  -- Cambia por tu esquema
ORDER BY 
    c.TABLE_NAME, 
    c.ORDINAL_POSITION, 
    s.INDEX_NAME, 
    s.SEQ_IN_INDEX;