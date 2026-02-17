# Módulo 01: Data Normalization

## Descripción General

Este módulo realiza la normalización completa de múltiples datasets aplicando principios de diseño de bases de datos relacional (1NF, 2NF, 3NF) y resolviendo solapamientos de dimensiones compartidas entre datasets relacionados.

## Funcionalidades Principales

### Normalización Estándar
- Atomización de datos (Primera Forma Normal - 1NF)
- Descomposición de tablas en dimensiones
- Creación de tablas de referencia (lookup tables)

### Corrección de Overlaps
Identificación y resolución de inconsistencias en las 3 tablas de dimensiones compartidas entre `application_train` y `previous_application`:
- `dim_name_contract_type`
- `dim_weekday_appr_process_start`
- `dim_name_type_suite`

## Procesamiento en Fases

El script principal ejecuta tres fases secuenciales:

### Fase 1: Normalización y optimización de diseño
Se procesan los datasets almacenados en db_input:
- `application_train.csv`
- `application_test.csv`
- `bureau_balance.csv`
- `bureau.csv`
- `credit_card_balance.csv`
- `installments_payments.csv`
- `POS_CASH_balance.csv`
- `previous_application.csv`

Se realizan las siguientes transformaciones:
- Atomización de `ORGANIZATION_TYPE`: se extrae el número de tipo en columna separada y se crea el atributo `ORGANIZATION_TYPE_2`.
- Se optimizan los datasets reemplazando por IDs en lugar de valores categóricos. Cada atributo categórico se descompone en:
    - Tabla Principal: Contiene solo IDs (referencias a dimensiones).
    - Tabla de Dimensión: Mapeo de ID → Valor original.
- Tablas de dimensiones en archivos CSV separados.

### Fase 2: Correcciones para datasets con solapamiento de dimensiones:
Dos datasets comparten algunas dimensiones en común:
- `application_train.csv`
- `previous_application.csv`

Dado que el mapeo realizado por pandas asigna automáticamente valores según el orden en que se suceden a lo largo de cada atributo, se aplican remapeos de IDs para alinar las dimensiones compartidas:

**Para `application_train`:**
- `NAME_CONTRACT_TYPE_ID`: Mapeo de 2 categorías.
- `WEEKDAY_APPR_PROCESS_START_ID`: Mapeo de 7 días (1 - MONDAY a 7 - SUNDAY).
- `NAME_TYPE_SUITE_ID`: Mapeo de 7 tipos.

**Para `previous_application`:**
- `WEEKDAY_APPR_PROCESS_START_ID`: Mapeo de 7 días.

Exporta:
- Datasets corregidos.
- Tres tablas de dimensiones comunes conciliadas con los datasets de referencia.

### Fase 3: Limpieza
Elimina directorios temporales de `application_train` y `previous_application` originales.

## Estructura de Salida

```
data/db_input/
├── application_test/
│   ├── application_test.csv
│   ├── dim_*.csv
│   └── ...
├── bureau/
│   ├── bureau.csv
│   ├── dim_*.csv
│   └── ...
├── common_dims/
│   ├── dim_name_contract_type.csv
│   ├── dim_weekday_appr_process_start.csv
│   └── dim_name_type_suite.csv
└── ...
```

## Ejecución

Ejecutar como script:

```bash
python 01_data_normalization/src/__main__.py
```

O ejecutar como módulo:

```bash
python -m 01_data_normalization
```
## Notas Importantes

1. El script espera los CSV de entrada en `../data/raw/`
2. Los archivos de salida se guardan en `../data/db_input/`
3. Los directorios temporales se limpian automáticamente al final.

## Tests

### test_content.py

Script principal que verifica que los datasets normalizados mantienen la integridad de los datos comparándolos con los originales.

**Datasets revisados:**
- `application_train`
- `bureau`
- `previous_application`

**Validaciones realizadas:**
1. **Estructura**: Verifica que el número de filas se mantiene
2. **Columnas**: Valida que todas las columnas esperadas estén presentes
3. **Contenido**: Compara valores entre datasets original y normalizado

### Ejecución de Tests

Ejecutar directamente:

```bash
python 01_data_normalization/tests/test_content.py
```

O bien como módulo:

```bash
python -m 01_data_normalization.tests.test_content
```

### Notas sobre las Validaciones

- Las columnas `ORGANIZATION_TYPE` y `ORGANIZATION_TYPE_2` se excluyen de la comparación ya que se transforman durante la normalización.
- Se tolera una diferencia máxima de `1e-5` en valores numéricos para permitir errores de redondeo.
- El script genera un resumen detallado de diferencias encontradas para facilitar el debugging.

## Requisitos

- pandas
- numpy
- pandasql
- pytest (opcional)


