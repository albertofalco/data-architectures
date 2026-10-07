# Bitácora 5: Incorporación de Llaves y Análisis de Esquema

## Contexto y objetivo

Durante el análisis del esquema de la base de datos en bitácoras anteriores, se identificó que las tablas de los esquemas data_arch_prod y data_arch_test carecían de integridad referencial formal. Para solucionar esta situación, se desarrolló el script db_ddl_keys.sql con el objetivo de incorporar llaves primarias (primary keys) y llaves foráneas (foreign keys) a las tablas del modelo de datos. Adicionalmente, se creó el script db_schema_analysis.sql para verificar que las modificaciones se aplicaron correctamente mediante consultas al diccionario de datos de MySQL.

## Incorporación de llaves primarias

Tablas dimensionales: Se generó un script dinámico que identifica columnas terminadas en “ID” dentro de las tablas con prefijo “dim” y construye las sentencias ALTER TABLE correspondientes:

```sql
ALTER TABLE dim_channel_type ADD PRIMARY KEY(CHANNEL_TYPE_ID);
ALTER TABLE dim_code_gender ADD PRIMARY KEY(CODE_GENDER_ID);
ALTER TABLE dim_code_reject_reason ADD PRIMARY KEY(CODE_REJECT_REASON_ID);
ALTER TABLE dim_credit_active ADD PRIMARY KEY(CREDIT_ACTIVE_ID);
ALTER TABLE dim_credit_currency ADD PRIMARY KEY(CREDIT_CURRENCY_ID);
ALTER TABLE dim_credit_type ADD PRIMARY KEY(CREDIT_TYPE_ID);
…
ALTER TABLE dim_weekday_appr_process_start ADD PRIMARY KEY(WEEKDAY_APPR_PROCESS_START_ID);
```

Tablas de hechos y de transacciones: Las tablas principales del modelo de datos recibieron llaves primarias compuestas, identificando de manera única cada registro mediante la combinación de columnas que relacionan con otras tablas:

```sql
ALTER TABLE application_train ADD PRIMARY KEY(SK_ID_CURR);
ALTER TABLE bureau ADD PRIMARY KEY(SK_ID_CURR, SK_ID_BUREAU);
ALTER TABLE previous_application ADD PRIMARY KEY(SK_ID_PREV, SK_ID_CURR);
```

Tablas sin llave primaria por valores duplicados: Algunas tablas transaccionales presentaban valores duplicados en las columnas candidatas a llave primaria, por lo que no fue posible crear una clave primaria formal. Para mantener un acceso eficiente a los datos, se crearon índices compuestos en su lugar:

```sql
ALTER TABLE bureau_balance ADD INDEX idx_bb_bureau (SK_ID_BUREAU);
ALTER TABLE credit_card_balance ADD INDEX idx_ccb_prev_curr (SK_ID_PREV, SK_ID_CURR);
ALTER TABLE installments_payments ADD INDEX idx_ip_prev_curr (SK_ID_PREV, SK_ID_CURR);
ALTER TABLE pos_cash_balance ADD INDEX idx_pcb_prev_curr (SK_ID_PREV, SK_ID_CURR);
```

## Incorporación de llaves foráneas

Para establecer la integridad referencial entre las tablas de hechos/datos transaccionales y las tablas dimensionales, se generó un script dinámico que construye las instrucciones ALTER TABLE con las restricciones FOREIGN KEY necesarias:

```sql
-- Tabla application_train
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_NAME_CONTRACT_TYPE_ID FOREIGN KEY (NAME_CONTRACT_TYPE_ID) REFERENCES dim_name_contract_type(NAME_CONTRACT_TYPE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_CODE_GENDER_ID FOREIGN KEY (CODE_GENDER_ID) REFERENCES dim_code_gender(CODE_GENDER_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_FLAG_OWN_CAR_ID FOREIGN KEY (FLAG_OWN_CAR_ID) REFERENCES dim_flag_own_car(FLAG_OWN_CAR_ID);
…
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_ORGANIZATION_TYPE_2_ID FOREIGN KEY (ORGANIZATION_TYPE_2_ID) REFERENCES dim_organization_type_2(ORGANIZATION_TYPE_2_ID);

-- Tabla bureau
ALTER TABLE bureau ADD CONSTRAINT fk_bureau_CREDIT_ACTIVE_ID FOREIGN KEY (CREDIT_ACTIVE_ID) REFERENCES dim_credit_active(CREDIT_ACTIVE_ID);
ALTER TABLE bureau ADD CONSTRAINT fk_bureau_CREDIT_CURRENCY_ID FOREIGN KEY (CREDIT_CURRENCY_ID) REFERENCES dim_credit_currency(CREDIT_CURRENCY_ID);
ALTER TABLE bureau ADD CONSTRAINT fk_bureau_CREDIT_TYPE_ID FOREIGN KEY (CREDIT_TYPE_ID) REFERENCES dim_credit_type(CREDIT_TYPE_ID);

-- Tabla bureau_balance
ALTER TABLE bureau_balance ADD CONSTRAINT fk_bureau_balance_STATUS_ID FOREIGN KEY (STATUS_ID) REFERENCES dim_status(STATUS_ID);

-- Tabla credit_card_balance
ALTER TABLE credit_card_balance ADD CONSTRAINT fk_credit_card_balance_NAME_CONTRACT_STATUS_ID FOREIGN KEY (NAME_CONTRACT_STATUS_ID) REFERENCES dim_name_contract_status(NAME_CONTRACT_STATUS_ID);

-- Tabla pos_cash_balance
ALTER TABLE pos_cash_balance ADD CONSTRAINT fk_pos_cash_balance_NAME_CONTRACT_STATUS_ID FOREIGN KEY (NAME_CONTRACT_STATUS_ID) REFERENCES dim_name_contract_status(NAME_CONTRACT_STATUS_ID);

-- Tabla previous_application
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_CONTRACT_TYPE_ID FOREIGN KEY (NAME_CONTRACT_TYPE_ID) REFERENCES dim_name_contract_type(NAME_CONTRACT_TYPE_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_WEEKDAY_APPR_PROCESS_START_ID FOREIGN KEY (WEEKDAY_APPR_PROCESS_START_ID) REFERENCES dim_weekday_appr_process_start(WEEKDAY_APPR_PROCESS_START_ID);
…
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_PRODUCT_COMBINATION_ID FOREIGN KEY (PRODUCT_COMBINATION_ID) REFERENCES dim_product_combination(PRODUCT_COMBINATION_ID);
```

## Control posterior a la ejecución

Con el objetivo de verificar que todas las modificaciones se aplicaron correctamente en el esquema de la base de datos, se desarrolló el script db_schema_analysis.sql. Este script utiliza las vistas del diccionario de datos de MySQL (INFORMATION_SCHEMA) para realizar un análisis exhaustivo del esquema.

```sql
-- Resumen de tablas
-- Esta consulta proporciona una visión general de todas las tablas en la base de datos, incluyendo la cantidad de registros y la cantidad de columnas por tabla.
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

-- Detalle de columnas con tipos y restricciones: 
-- Esta consulta muestra el detalle completo de cada columna, incluyendo tipo de dato, si permite valores nulos, si es llave primaria o foránea, y el valor por defecto.
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

-- Análisis de llaves foráneas
-- Esta consulta identifica todas las restricciones de llave foránea en la base de datos, mostrando la tabla y columna que contiene la restricción, así como la tabla y columna a la que hace referencia
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

-- Diccionario de columnas con índices
-- Esta consulta combina información de columnas e índices, permitiendo verificar qué columnas forman parte de índices y si estos son únicos o no.
SELECT 
    c.TABLE_NAME AS 'Tabla',
    c.COLUMN_NAME AS 'Columna',
    c.ORDINAL_POSITION AS 'Posición',
    c.COLUMN_TYPE AS 'Tipo Detallado',
    c.IS_NULLABLE AS 'Nulable',
    c.COLUMN_KEY AS 'Llave',
    c.EXTRA AS 'Extra',
    s.INDEX_NAME AS 'Indice',
    s.SEQ_IN_INDEX AS 'Orden en Indice',
    s.NON_UNIQUE AS 'Es Único'
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
```
