-----------------------------------------------------------------------------------------------------------------------------
-- 1. Incorporacion de llaves primarias a tablas de dimensiones, hechos y transaccionales.
-----------------------------------------------------------------------------------------------------------------------------

-- Script para generar sentencias ALTER TABLE para agregar llaves primarias a tablas de dimensiones.
-- Criterio: Columna terminada en "ID" es la PK.
SELECT 
    CONCAT(
        'ALTER TABLE `', TABLE_NAME, 
        '` ADD PRIMARY KEY(`', COLUMN_NAME, '`);'
    ) AS alter_statement
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'data_arch_prod'   -- tu base de datos
  AND TABLE_NAME LIKE 'dim%'            -- prefijo de tabla
  AND COLUMN_NAME LIKE '%ID%';          -- columna que contenga "ID"

-- Script para generar sentencias ALTER TABLE para agregar llaves primarias a tablas de hechos y transaccionales.
ALTER TABLE dim_channel_type ADD PRIMARY KEY(CHANNEL_TYPE_ID);
ALTER TABLE dim_code_gender ADD PRIMARY KEY(CODE_GENDER_ID);
ALTER TABLE dim_code_reject_reason ADD PRIMARY KEY(CODE_REJECT_REASON_ID);
ALTER TABLE dim_credit_active ADD PRIMARY KEY(CREDIT_ACTIVE_ID);
ALTER TABLE dim_credit_currency ADD PRIMARY KEY(CREDIT_CURRENCY_ID);
ALTER TABLE dim_credit_type ADD PRIMARY KEY(CREDIT_TYPE_ID);
ALTER TABLE dim_emergencystate_mode ADD PRIMARY KEY(EMERGENCYSTATE_MODE_ID);
ALTER TABLE dim_flag_last_appl_per_contract ADD PRIMARY KEY(FLAG_LAST_APPL_PER_CONTRACT_ID);
ALTER TABLE dim_flag_own_car ADD PRIMARY KEY(FLAG_OWN_CAR_ID);
ALTER TABLE dim_flag_own_realty ADD PRIMARY KEY(FLAG_OWN_REALTY_ID);
ALTER TABLE dim_fondkapremont_mode ADD PRIMARY KEY(FONDKAPREMONT_MODE_ID);
ALTER TABLE dim_housetype_mode ADD PRIMARY KEY(HOUSETYPE_MODE_ID);
ALTER TABLE dim_name_cash_loan_purpose ADD PRIMARY KEY(NAME_CASH_LOAN_PURPOSE_ID);
ALTER TABLE dim_name_client_type ADD PRIMARY KEY(NAME_CLIENT_TYPE_ID);
ALTER TABLE dim_name_contract_status ADD PRIMARY KEY(NAME_CONTRACT_STATUS_ID);
ALTER TABLE dim_name_contract_type ADD PRIMARY KEY(NAME_CONTRACT_TYPE_ID);
ALTER TABLE dim_name_education_type ADD PRIMARY KEY(NAME_EDUCATION_TYPE_ID);
ALTER TABLE dim_name_family_status ADD PRIMARY KEY(NAME_FAMILY_STATUS_ID);
ALTER TABLE dim_name_goods_category ADD PRIMARY KEY(NAME_GOODS_CATEGORY_ID);
ALTER TABLE dim_name_housing_type ADD PRIMARY KEY(NAME_HOUSING_TYPE_ID);
ALTER TABLE dim_name_income_type ADD PRIMARY KEY(NAME_INCOME_TYPE_ID);
ALTER TABLE dim_name_payment_type ADD PRIMARY KEY(NAME_PAYMENT_TYPE_ID);
ALTER TABLE dim_name_portfolio ADD PRIMARY KEY(NAME_PORTFOLIO_ID);
ALTER TABLE dim_name_product_type ADD PRIMARY KEY(NAME_PRODUCT_TYPE_ID);
ALTER TABLE dim_name_seller_industry ADD PRIMARY KEY(NAME_SELLER_INDUSTRY_ID);
ALTER TABLE dim_name_type_suite ADD PRIMARY KEY(NAME_TYPE_SUITE_ID);
ALTER TABLE dim_name_yield_group ADD PRIMARY KEY(NAME_YIELD_GROUP_ID);
ALTER TABLE dim_occupation_type ADD PRIMARY KEY(OCCUPATION_TYPE_ID);
ALTER TABLE dim_organization_type_2 ADD PRIMARY KEY(ORGANIZATION_TYPE_2_ID);
ALTER TABLE dim_organization_type ADD PRIMARY KEY(ORGANIZATION_TYPE_ID);
ALTER TABLE dim_product_combination ADD PRIMARY KEY(PRODUCT_COMBINATION_ID);
ALTER TABLE dim_status ADD PRIMARY KEY(STATUS_ID);
ALTER TABLE dim_wallsmaterial_mode ADD PRIMARY KEY(WALLSMATERIAL_MODE_ID);
ALTER TABLE dim_weekday_appr_process_start ADD PRIMARY KEY(WEEKDAY_APPR_PROCESS_START_ID);

-- Script para generar sentencias ALTER TABLE para agregar llaves primarias a tablas de hechos y transaccionales.
ALTER TABLE application_train ADD PRIMARY KEY(SK_ID_CURR);
ALTER TABLE bureau ADD PRIMARY KEY(SK_ID_CURR, SK_ID_BUREAU);
ALTER TABLE bureau_balance ADD PRIMARY KEY(SK_ID_BUREAU); -- NO SE CREA PRIMARY KEY POR VALORES DUPLICADOS.
ALTER TABLE credit_card_balance ADD PRIMARY KEY(SK_ID_PREV, SK_ID_CURR); -- NO SE CREA PRIMARY KEY POR VALORES DUPLICADOS.
ALTER TABLE installments_payments ADD PRIMARY KEY(SK_ID_PREV, SK_ID_CURR); -- NO SE CREA PRIMARY KEY POR VALORES DUPLICADOS.
ALTER TABLE pos_cash_balance ADD PRIMARY KEY(SK_ID_PREV, SK_ID_CURR); -- NO SE CREA PRIMARY KEY POR VALORES DUPLICADOS.
ALTER TABLE previous_application ADD PRIMARY KEY(SK_ID_PREV, SK_ID_CURR);
-- ALTER TABLE previous_application DROP PRIMARY KEY;

-- Se crean indices para las tablas que no poseen primary key.
ALTER TABLE bureau_balance ADD INDEX idx_bb_bureau (SK_ID_BUREAU);
ALTER TABLE credit_card_balance ADD INDEX idx_ccb_prev_curr (SK_ID_PREV, SK_ID_CURR);
ALTER TABLE installments_payments ADD INDEX idx_ip_prev_curr (SK_ID_PREV, SK_ID_CURR);
ALTER TABLE pos_cash_balance ADD INDEX idx_pcb_prev_curr (SK_ID_PREV, SK_ID_CURR);

-- Control final de modificaciones: Diccionario de columnas + índices
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

-----------------------------------------------------------------------------------------------------------------------------
-- 2. Incorporacion de llaves foreaneas a tablas de hechos y transaccionales.
-----------------------------------------------------------------------------------------------------------------------------

-- Consulta de claves foraneas.
USE data_arch_test;
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
    c.TABLE_SCHEMA = 'data_arch_test'
ORDER BY 
    c.TABLE_NAME, c.ORDINAL_POSITION;

-- Tabla: application_train
-- Generador de instrucciones SQL.
SELECT 
    CONCAT(
        'ALTER TABLE ', c.TABLE_NAME,
        ' ADD CONSTRAINT fk_', c.TABLE_NAME, '_', c.COLUMN_NAME,
        ' FOREIGN KEY (', c.COLUMN_NAME, ') REFERENCES ',
        'dim_', LOWER(REPLACE(c.COLUMN_NAME, '_ID', '')),
        '(', c.COLUMN_NAME, ');'
    ) AS alter_statement
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_SCHEMA = 'data_arch_test'
  AND c.TABLE_NAME = 'application_train'
  AND c.COLUMN_NAME LIKE '%_ID';

ALTER TABLE application_train ADD CONSTRAINT fk_application_train_NAME_CONTRACT_TYPE_ID FOREIGN KEY (NAME_CONTRACT_TYPE_ID) REFERENCES dim_name_contract_type(NAME_CONTRACT_TYPE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_CODE_GENDER_ID FOREIGN KEY (CODE_GENDER_ID) REFERENCES dim_code_gender(CODE_GENDER_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_FLAG_OWN_CAR_ID FOREIGN KEY (FLAG_OWN_CAR_ID) REFERENCES dim_flag_own_car(FLAG_OWN_CAR_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_FLAG_OWN_REALTY_ID FOREIGN KEY (FLAG_OWN_REALTY_ID) REFERENCES dim_flag_own_realty(FLAG_OWN_REALTY_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_NAME_TYPE_SUITE_ID FOREIGN KEY (NAME_TYPE_SUITE_ID) REFERENCES dim_name_type_suite(NAME_TYPE_SUITE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_NAME_INCOME_TYPE_ID FOREIGN KEY (NAME_INCOME_TYPE_ID) REFERENCES dim_name_income_type(NAME_INCOME_TYPE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_NAME_EDUCATION_TYPE_ID FOREIGN KEY (NAME_EDUCATION_TYPE_ID) REFERENCES dim_name_education_type(NAME_EDUCATION_TYPE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_NAME_FAMILY_STATUS_ID FOREIGN KEY (NAME_FAMILY_STATUS_ID) REFERENCES dim_name_family_status(NAME_FAMILY_STATUS_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_NAME_HOUSING_TYPE_ID FOREIGN KEY (NAME_HOUSING_TYPE_ID) REFERENCES dim_name_housing_type(NAME_HOUSING_TYPE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_OCCUPATION_TYPE_ID FOREIGN KEY (OCCUPATION_TYPE_ID) REFERENCES dim_occupation_type(OCCUPATION_TYPE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_WEEKDAY_APPR_PROCESS_START_ID FOREIGN KEY (WEEKDAY_APPR_PROCESS_START_ID) REFERENCES dim_weekday_appr_process_start(WEEKDAY_APPR_PROCESS_START_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_ORGANIZATION_TYPE_ID FOREIGN KEY (ORGANIZATION_TYPE_ID) REFERENCES dim_organization_type(ORGANIZATION_TYPE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_FONDKAPREMONT_MODE_ID FOREIGN KEY (FONDKAPREMONT_MODE_ID) REFERENCES dim_fondkapremont_mode(FONDKAPREMONT_MODE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_HOUSETYPE_MODE_ID FOREIGN KEY (HOUSETYPE_MODE_ID) REFERENCES dim_housetype_mode(HOUSETYPE_MODE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_WALLSMATERIAL_MODE_ID FOREIGN KEY (WALLSMATERIAL_MODE_ID) REFERENCES dim_wallsmaterial_mode(WALLSMATERIAL_MODE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_EMERGENCYSTATE_MODE_ID FOREIGN KEY (EMERGENCYSTATE_MODE_ID) REFERENCES dim_emergencystate_mode(EMERGENCYSTATE_MODE_ID);
ALTER TABLE application_train ADD CONSTRAINT fk_application_train_ORGANIZATION_TYPE_2_ID FOREIGN KEY (ORGANIZATION_TYPE_2_ID) REFERENCES dim_organization_type_2(ORGANIZATION_TYPE_2_ID);

-- Tabla: bureau
-- Generador de instrucciones SQL.
SELECT 
    CONCAT(
        'ALTER TABLE ', c.TABLE_NAME,
        ' ADD CONSTRAINT fk_', c.TABLE_NAME, '_', c.COLUMN_NAME,
        ' FOREIGN KEY (', c.COLUMN_NAME, ') REFERENCES ',
        'dim_', LOWER(REPLACE(c.COLUMN_NAME, '_ID', '')),
        '(', c.COLUMN_NAME, ');'
    ) AS alter_statement
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_SCHEMA = 'data_arch_test'
  AND c.TABLE_NAME = 'bureau'
  AND c.COLUMN_NAME LIKE '%_ID';

ALTER TABLE bureau ADD CONSTRAINT fk_bureau_CREDIT_ACTIVE_ID FOREIGN KEY (CREDIT_ACTIVE_ID) REFERENCES dim_credit_active(CREDIT_ACTIVE_ID);
ALTER TABLE bureau ADD CONSTRAINT fk_bureau_CREDIT_CURRENCY_ID FOREIGN KEY (CREDIT_CURRENCY_ID) REFERENCES dim_credit_currency(CREDIT_CURRENCY_ID);
ALTER TABLE bureau ADD CONSTRAINT fk_bureau_CREDIT_TYPE_ID FOREIGN KEY (CREDIT_TYPE_ID) REFERENCES dim_credit_type(CREDIT_TYPE_ID);

-- Tabla: bureau_balance
-- Generador de instrucciones SQL.
SELECT 
    CONCAT(
        'ALTER TABLE ', c.TABLE_NAME,
        ' ADD CONSTRAINT fk_', c.TABLE_NAME, '_', c.COLUMN_NAME,
        ' FOREIGN KEY (', c.COLUMN_NAME, ') REFERENCES ',
        'dim_', LOWER(REPLACE(c.COLUMN_NAME, '_ID', '')),
        '(', c.COLUMN_NAME, ');'
    ) AS alter_statement
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_SCHEMA = 'data_arch_test'
  AND c.TABLE_NAME = 'bureau_balance'
  AND c.COLUMN_NAME LIKE '%_ID';

ALTER TABLE bureau_balance ADD CONSTRAINT fk_bureau_balance_STATUS_ID FOREIGN KEY (STATUS_ID) REFERENCES dim_status(STATUS_ID);

-- Tabla: credit_card_balance
-- Generador de instrucciones SQL.
SELECT 
    CONCAT(
        'ALTER TABLE ', c.TABLE_NAME,
        ' ADD CONSTRAINT fk_', c.TABLE_NAME, '_', c.COLUMN_NAME,
        ' FOREIGN KEY (', c.COLUMN_NAME, ') REFERENCES ',
        'dim_', LOWER(REPLACE(c.COLUMN_NAME, '_ID', '')),
        '(', c.COLUMN_NAME, ');'
    ) AS alter_statement
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_SCHEMA = 'data_arch_test'
  AND c.TABLE_NAME = 'credit_card_balance'
  AND c.COLUMN_NAME LIKE '%_ID';

ALTER TABLE credit_card_balance ADD CONSTRAINT fk_credit_card_balance_NAME_CONTRACT_STATUS_ID FOREIGN KEY (NAME_CONTRACT_STATUS_ID) REFERENCES dim_name_contract_status(NAME_CONTRACT_STATUS_ID);

-- Tabla: installments_payments
-- Generador de instrucciones SQL.
SELECT 
    CONCAT(
        'ALTER TABLE ', c.TABLE_NAME,
        ' ADD CONSTRAINT fk_', c.TABLE_NAME, '_', c.COLUMN_NAME,
        ' FOREIGN KEY (', c.COLUMN_NAME, ') REFERENCES ',
        'dim_', LOWER(REPLACE(c.COLUMN_NAME, '_ID', '')),
        '(', c.COLUMN_NAME, ');'
    ) AS alter_statement
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_SCHEMA = 'data_arch_test'
  AND c.TABLE_NAME = 'installments_payments'
  AND c.COLUMN_NAME LIKE '%_ID';
  
-- No contiene columnas susceptibles de ser asignadas como llaves foraneas.

-- Tabla: pos_cash_balance
-- Generador de instrucciones SQL.
SELECT 
    CONCAT(
        'ALTER TABLE ', c.TABLE_NAME,
        ' ADD CONSTRAINT fk_', c.TABLE_NAME, '_', c.COLUMN_NAME,
        ' FOREIGN KEY (', c.COLUMN_NAME, ') REFERENCES ',
        'dim_', LOWER(REPLACE(c.COLUMN_NAME, '_ID', '')),
        '(', c.COLUMN_NAME, ');'
    ) AS alter_statement
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_SCHEMA = 'data_arch_test'
  AND c.TABLE_NAME = 'pos_cash_balance'
  AND c.COLUMN_NAME LIKE '%_ID';
  
ALTER TABLE pos_cash_balance ADD CONSTRAINT fk_pos_cash_balance_NAME_CONTRACT_STATUS_ID FOREIGN KEY (NAME_CONTRACT_STATUS_ID) REFERENCES dim_name_contract_status(NAME_CONTRACT_STATUS_ID);
-- ALTER TABLE pos_cash_balance DROP CONSTRAINT fk_pos_cash_balance_NAME_CONTRACT_STATUS_ID;

-- Tabla: previous_application
-- Generador de instrucciones SQL.
SELECT 
    CONCAT(
        'ALTER TABLE ', c.TABLE_NAME,
        ' ADD CONSTRAINT fk_', c.TABLE_NAME, '_', c.COLUMN_NAME,
        ' FOREIGN KEY (', c.COLUMN_NAME, ') REFERENCES ',
        'dim_', LOWER(REPLACE(c.COLUMN_NAME, '_ID', '')),
        '(', c.COLUMN_NAME, ');'
    ) AS alter_statement
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_SCHEMA = 'data_arch_test'
  AND c.TABLE_NAME = 'previous_application'
  AND c.COLUMN_NAME LIKE '%_ID';  

ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_CONTRACT_TYPE_ID FOREIGN KEY (NAME_CONTRACT_TYPE_ID) REFERENCES dim_name_contract_type(NAME_CONTRACT_TYPE_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_WEEKDAY_APPR_PROCESS_START_ID FOREIGN KEY (WEEKDAY_APPR_PROCESS_START_ID) REFERENCES dim_weekday_appr_process_start(WEEKDAY_APPR_PROCESS_START_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_FLAG_LAST_APPL_PER_CONTRACT_ID FOREIGN KEY (FLAG_LAST_APPL_PER_CONTRACT_ID) REFERENCES dim_flag_last_appl_per_contract(FLAG_LAST_APPL_PER_CONTRACT_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_CASH_LOAN_PURPOSE_ID FOREIGN KEY (NAME_CASH_LOAN_PURPOSE_ID) REFERENCES dim_name_cash_loan_purpose(NAME_CASH_LOAN_PURPOSE_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_CONTRACT_STATUS_ID FOREIGN KEY (NAME_CONTRACT_STATUS_ID) REFERENCES dim_name_contract_status(NAME_CONTRACT_STATUS_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_PAYMENT_TYPE_ID FOREIGN KEY (NAME_PAYMENT_TYPE_ID) REFERENCES dim_name_payment_type(NAME_PAYMENT_TYPE_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_CODE_REJECT_REASON_ID FOREIGN KEY (CODE_REJECT_REASON_ID) REFERENCES dim_code_reject_reason(CODE_REJECT_REASON_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_TYPE_SUITE_ID FOREIGN KEY (NAME_TYPE_SUITE_ID) REFERENCES dim_name_type_suite(NAME_TYPE_SUITE_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_CLIENT_TYPE_ID FOREIGN KEY (NAME_CLIENT_TYPE_ID) REFERENCES dim_name_client_type(NAME_CLIENT_TYPE_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_GOODS_CATEGORY_ID FOREIGN KEY (NAME_GOODS_CATEGORY_ID) REFERENCES dim_name_goods_category(NAME_GOODS_CATEGORY_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_PORTFOLIO_ID FOREIGN KEY (NAME_PORTFOLIO_ID) REFERENCES dim_name_portfolio(NAME_PORTFOLIO_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_PRODUCT_TYPE_ID FOREIGN KEY (NAME_PRODUCT_TYPE_ID) REFERENCES dim_name_product_type(NAME_PRODUCT_TYPE_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_CHANNEL_TYPE_ID FOREIGN KEY (CHANNEL_TYPE_ID) REFERENCES dim_channel_type(CHANNEL_TYPE_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_SELLER_INDUSTRY_ID FOREIGN KEY (NAME_SELLER_INDUSTRY_ID) REFERENCES dim_name_seller_industry(NAME_SELLER_INDUSTRY_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_NAME_YIELD_GROUP_ID FOREIGN KEY (NAME_YIELD_GROUP_ID) REFERENCES dim_name_yield_group(NAME_YIELD_GROUP_ID);
ALTER TABLE previous_application ADD CONSTRAINT fk_previous_application_PRODUCT_COMBINATION_ID FOREIGN KEY (PRODUCT_COMBINATION_ID) REFERENCES dim_product_combination(PRODUCT_COMBINATION_ID);

