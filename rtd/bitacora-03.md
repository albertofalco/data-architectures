# Bitácora 3: Scripts y comandos DDL

## Consulta de los tipos de datos y restricciones

Se accede a MySQL Workbench. Se utilizan las credenciales de `admin`. Se diseña un script para obtener el listado de las columnas de cada una de las tablas e información aclaratoria.

```sql
-- Selecciona la base de datos con la que vas a trabajar
USE data_arch_prod;

-- Consulta las columnas de todas las tablas dentro del esquema especificado
SELECT
    TABLE_NAME AS 'Tabla', -- Nombre de la tabla
    COLUMN_NAME AS 'Columna', -- Nombre de la columna
    ORDINAL_POSITION AS 'Posición', -- Orden de la columna dentro de la tabla
    COLUMN_TYPE AS 'Tipo Detallado', -- Tipo de dato con longitud/precisión (ej: varchar(255), int(11))
    IS_NULLABLE AS 'Nulable', -- Indica si la columna permite valores NULL (YES/NO)
    COLUMN_KEY AS 'Llave', -- Tipo de llave: PRI (Primaria), UNI (Única), MUL (Indexada)
    EXTRA AS 'Extra' -- Información adicional (ej: auto_increment)
FROM
    INFORMATION_SCHEMA.COLUMNS -- Vista del diccionario de datos con metainformación de columnas
WHERE
    TABLE_SCHEMA = 'data_arch_prod' -- Filtra solo las tablas de este esquema/base de datos
ORDER BY
    TABLE_NAME, -- Ordena primero por nombre de tabla
    ORDINAL_POSITION; -- Luego por posición de columna dentro de cada tabla
```

## Operaciones DDL (Data Definition Language)

De la ejecución de las instrucciones SQL para crear las claves primarias y foráneas, se detectó que:

- El campo `name_contract_status` se encuentra compartido entre algunas tablas, con diferente asignación de valores entre ellas.
- El establecimiento de tipos de campo y claves primarias y foráneas no está funcionando correctamente en el entorno SQL ya creado, por lo que es más conveniente revisar los tipos de datos y relaciones en el módulo `02_database_connections`.

Para resolver estos inconvenientes, se procedió a la refactorización de los módulos `01_data_normalization` y `02_database_connections`.
