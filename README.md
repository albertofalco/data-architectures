# data-architectures

Data Architectures for Risk Management and Audit

## Módulos

### 01_data_normalization

**Descripción:** Script de normalización de bases de datos que aplica principios de diseño relacional (1NF, 2NF, 3NF) a múltiples datasets, incluyendo atomización de valores, creación de tablas de dimensiones y resolución de solapamientos de dimensiones compartidas.

**Script principal:** [`src/__main__.py`](01_data_normalization/src/__main__.py)

- **Funcionalidades:**
  - Atomización de datos (Primera Forma Normal - 1NF)
  - Descomposición de tablas en dimensiones y tablas de referencia
  - Resolución de overlaps en dimensiones compartidas entre `application_train` y `previous_application`
  - Procesamiento en 4 fases: normalización estándar, normalización con overlap, correcciones de overlap y limpieza
  - Exportación de datasets normalizados y tablas de dimensiones en CSV

- **Tests:**
  - `test_content.py`: Valida la integridad del contenido comparando datasets normalizados con los originales, verificando estructura (shape), columnas y valores de datasets como `application_train`, `bureau` y `previous_application`

---

### 02_database_connections

**Descripción:** Herramienta para automatizar la carga de datos desde archivos CSV a una base de datos MySQL, con funcionalidades de creación automática de esquemas, validación de integridad de datos y control de sincronización.

**Script principal:** [`src/__main__.py`](02_database_connections/src/__main__.py)

- **Funcionalidades:**
  - Conexión a servidor MySQL con configuración vía argumentos o variables de entorno
  - Creación automática de base de datos si no existe
  - Detección dinámica de archivos CSV
  - Inferencia automática de tipos de datos
  - Carga masiva optimizada de datos usando `LOAD DATA LOCAL INFILE`

- **Tests:**
  - `test_db_connection.py`: Verifica la conectividad a la base de datos usando tanto `mysql-connector-python` como `SQLAlchemy`
  - `test_table_names.py`: Compara nombres de tablas en MySQL con archivos CSV en la carpeta para validar sincronización
  - `test_integrity.py`: Control de contenido de tablas verificando integridad comparándolas con archivos fuente, validando nombres de tablas, estructura (shape), columnas y valores

---
