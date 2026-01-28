# Script de Normalización de Base de Datos

## Descripción General

Este script realiza la normalización completa de múltiples datasets aplicando principios de diseño de bases de datos relacional (1NF, 2NF, 3NF) y resolviendo solapamientos de dimensiones compartidas.

## Funcionalidades Principales

### 1. **Normalización Estándar**
- Atomización de datos (Primera Forma Normal - 1NF)
- Descomposición de tablas en dimensiones
- Creación de tablas de referencia (lookup tables)

### 2. **Corrección de Overlaps**
Identificación y resolución de inconsistencias en las 3 tablas de dimensiones compartidas entre `application_train` y `previous_application`:
- `dim_name_contract_type`
- `dim_weekday_appr_process_start`
- `dim_name_type_suite`

### 3. **Procesamiento en Fases**

El script ejecuta 4 fases secuenciales:

#### Fase 1: Normalización Estándar
Procesa 6 datasets sin dependencias:
- `application_test.csv`
- `bureau_balance.csv`
- `bureau.csv`
- `credit_card_balance.csv`
- `installments_payments.csv`
- `POS_CASH_balance.csv`

Cada dataset genera:
- Dataset normalizado con IDs en lugar de valores categóricos
- Tablas de dimensiones en archivos CSV separados

#### Fase 2: Normalización con Overlap
Procesa 2 datasets que comparten dimensiones:
- `application_train.csv`
- `previous_application.csv`

*Nota: Las dimensiones NO se exportan en esta fase*

#### Fase 3: Correcciones de Overlap
Aplica remapeos de IDs para alinear las dimensiones compartidas:

**Para `application_train`:**
- `NAME_CONTRACT_TYPE_ID`: Mapeo de 2 categorías
- `WEEKDAY_APPR_PROCESS_START_ID`: Mapeo de 7 días
- `NAME_TYPE_SUITE_ID`: Mapeo de 7 tipos

**Para `previous_application`:**
- `WEEKDAY_APPR_PROCESS_START_ID`: Mapeo de 7 días

Exporta:
- Datasets corregidos
- 3 tablas de dimensiones de referencia estandarizadas
- Archivo ZIP comprimido (`overlap_fix.zip`)

#### Fase 4: Limpieza
Elimina directorios temporales de `application_train` y `previous_application` originales.

## Estructura de Salida

```
db_input/
├── application_test/
│   ├── application_test.csv
│   ├── dim_*.csv
│   └── ...
├── bureau/
│   ├── bureau.csv
│   ├── dim_*.csv
│   └── ...
├── ...
└── overlap_fix/
    ├── application_train.csv
    ├── previous_application.csv
    ├── dim_name_contract_type.csv
    ├── dim_weekday_appr_process_start.csv
    ├── dim_name_type_suite.csv
    └── (+ overlap_fix.zip)
```

## Uso

```bash
cd src/
python db_normalization.py
```

## Transformaciones Aplicadas

### Primera Forma Normal (1NF)
- Atomización de `ORGANIZATION_TYPE`: Extrae el número de tipo en columna separada `ORGANIZATION_TYPE_2`

### Dimensiones Estándar
Cada atributo categónico se descompone en:
- **Tabla Principal**: Contiene solo IDs (referencias a dimensiones)
- **Tabla de Dimensión**: Mapeo de ID → Valor original

### Mappeo de Weekdays Estandarizado
```
1 = MONDAY
2 = TUESDAY
3 = WEDNESDAY
4 = THURSDAY
5 = FRIDAY
6 = SATURDAY
7 = SUNDAY
```

## Requisitos

- Python 3.7+
- pandas
- numpy

## Notas Importantes

1. El script espera los CSV de entrada en `../../data/raw/`
2. Los archivos de salida se guardan en `../../db_input/`
3. Los directorios temporales se limpian automáticamente al final
4. El archivo `overlap_fix.zip` contiene una versión comprimida de los datos corregidos
5. Los IDs se convierten a `Int64` para manejar correctamente valores nulos
