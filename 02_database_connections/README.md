# Módulo 02: Database Connections

## Descripción General

Herramienta en Python para automatizar la carga de datos desde archivos CSV a una base de datos MySQL, incluyendo funcionalidades de creación automática de esquemas, validación de integridad de datos y control de sincronización entre archivos y tablas.

## Estructura del Proyecto

```
02_database_connections/
├── src/
│   ├── __main__.py                 # Script principal de carga
│   └── ...
├── tests/
│   ├── test_db_connection.py       # Verificación de conectividad
│   ├── test_table_names.py         # Validación de sincronización
│   ├── test_integrity.py           # Verificación de integridad
│   └── __init__.py
├── data/
│   └── db_input/                   # Carpeta de datos CSV
├── requirements.txt                # Dependencias
└── README.md                       # Este archivo
```

## Requisitos

- Python 3.8+
- Acceso a un servidor MySQL (local o remoto)
- Servidor MySQL con permisos de creación de bases de datos

## Instalación

1. Clona o descarga este repositorio
2. Crea y activa un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Preparación de Datos

Coloca tus archivos CSV en la carpeta `data/db_input/`:

```
02_database_connections/
├── data/
│   └── db_input/
│       ├── application_train.csv
│       ├── bureau.csv
│       └── ...
```

**Requisitos del CSV:**
- Archivo debe tener extensión `.csv`
- Primera fila debe contener los nombres de las columnas (encabezados)
- Los valores deben estar separados por comas (`,`)
- Valores de texto deben estar entre comillas (`"`)

---

## Script Principal: src/__main__.py

### Descripción

Automatiza el proceso completo de carga de datos CSV a MySQL:

1. **Conexión a la base de datos**: Se conecta al servidor MySQL
2. **Creación de base de datos**: Crea la BD si no existe
3. **Detección de archivos**: Busca todos los archivos `.csv` en la carpeta `data/db_input/`
4. **Creación automática de tablas**: Infiere tipos de datos y crea tablas
5. **Carga de datos**: Importa los datos usando `LOAD DATA LOCAL INFILE` (carga masiva optimizada)

### Funcionamiento

#### Paso 1: Configuración de Conexión

```bash
python -m 02_database_connections \
  --host 127.0.0.1 \
  --user root \
  --password tu_password \
  --database datos_normalizados
```

- Crea la base de datos si no existe
- Establece la conexión y prepara el cursor

#### Paso 2: Procesamiento de Archivos CSV

Para cada archivo `.csv` en `data/db_input/`:

1. **Lectura con Pandas**
   - Lee el CSV completo en memoria
   - Convierte valores `NaN` a `None` para compatibilidad con MySQL

2. **Inferencia de Tipos de Datos**
   - Analiza el tipo de datos de cada columna en Pandas
   - Mapea automáticamente a tipos SQL:
     - `int` → `INT`
     - `float` → `FLOAT`
     - Otros → `TEXT`

3. **Creación de Tabla**

4. **Limpieza de Datos Previos**
   - `TRUNCATE TABLE` elimina registros anteriores (si la tabla ya existía)

5. **Carga Masiva de Datos**
   - Utiliza `LOAD DATA LOCAL INFILE` para carga optimizada
   - Especifica delimitadores: comas (`,`)
   - Ignora la primera fila (encabezados)
   - Es mucho más rápido que inserciones individuales

#### Paso 3: Confirmación y Cierre
- Confirma los cambios con `COMMIT`
- Cierra conexiones y cursores

### Argumentos

| Argumento | Requerido | Descripción |
|-----------|-----------|-------------|
| `--host` | Sí | Dirección del servidor MySQL (ej: `127.0.0.1`) |
| `--user` | Sí | Usuario de MySQL (ej: `root`) |
| `--password` | Sí | Contraseña del usuario |
| `--database` | Sí | Nombre de la BD a crear/usar |

### Ejemplo de Uso

```bash
# Conexión a servidor local
python -m 02_database_connections \
  --host 127.0.0.1 \
  --user root \
  --password tu_password \
  --database datos_normalizados
```

### Notas Importantes

1. **`LOAD DATA LOCAL INFILE` habilitado**: El script establece `allow_local_infile=True` en la conexión
2. **Permisos del servidor**: Asegúrate de que tu servidor MySQL permite `local_infile`
3. **Truncado automático**: Las tablas se vacían antes de cargar (reemplaza datos anteriores)
4. **Tipos de datos simplificados**: Solo usa INT, FLOAT y TEXT (considera SQLAlchemy para mayor flexibilidad)

---

## Tests

El módulo incluye tres suites de tests para validar diferentes aspectos de la conexión y carga de datos.

### test_db_connection.py

Verifica la conectividad a la base de datos usando dos métodos diferentes:

**Métodos probados:**
- `mysql-connector-python`: Conexión nativa a MySQL
- `SQLAlchemy`: ORM con driver MySQL

**Validaciones:**
- Conexión exitosa al servidor
- Selección de base de datos
- Consulta de datos de tabla `application_train`

**Ejecución:**
```bash
python -m pytest tests/test_db_connection.py
# O directamente:
python tests/test_db_connection.py
```

---

### test_table_names.py

Valida la sincronización entre los archivos CSV disponibles y las tablas existentes en la base de datos MySQL.

**Funcionalidades:**
- Verifica que todos los CSVs tienen tablas correspondientes
- Detecta archivos CSV que aún no se han cargado
- Encuentra tablas huérfanas (sin archivo CSV de origen)
- Auditoría de datos

**Análisis comparativo:**

Realiza 3 operaciones de conjuntos:

1. **Coincidencias** (`intersection`)
   - Archivos CSV que tienen tabla en BD
   - Estado: ✅ Sincronizado

2. **Solo en BD** (`difference`)
   - Tablas sin archivo CSV correspondiente
   - Causa probable: CSV fue eliminado o renombrado
   - Estado: ⚠️ Posible inconsistencia

3. **Solo en carpeta** (`difference`)
   - Archivos CSV sin tabla en BD
   - Causa probable: CSV no ha sido cargado aún
   - Estado: 📂 Pendiente de carga

**Argumentos:**
```bash
python tests/test_table_names.py \
  --host 127.0.0.1 \
  --user root \
  --password password123 \
  --database mi_base_datos
```

**Salida esperada:**
```
──────────────────────────────
RESUMEN DE COMPARACIÓN
──────────────────────────────
✅ Coincidencias (8):
  - application_test
  - application_train
  - bureau
  - bureau_balance
  - credit_card_balance
  - installments_payments
  - POS_CASH_balance
  - previous_application

⚠️ Tablas en DB sin archivo CSV (0):

📂 Archivos CSV sin tabla en DB (0):
```

**Ejecución:**
```bash
python -m pytest tests/test_table_names.py
# O directamente con argumentos:
python tests/test_table_names.py --host 127.0.0.1 --user root --password pwd --database db
```

---

### test_integrity.py

Control de contenido de tablas verificando integridad comparándolas con archivos fuente.

**Validaciones realizadas:**
1. **Validación de nombres de tablas**: Compara tablas en BD vs archivos CSV
2. **Validación de estructura (shape)**: Verifica que filas y columnas coincidan
3. **Validación de esquema**: Comprueba nombres y orden de columnas
4. **Comparación de contenido**: Validación celda por celda con tolerancia en decimales

**Argumentos:**
```bash
python tests/test_integrity.py \
  --host 127.0.0.1 \
  --user root \
  --password password123 \
  --database mi_base_datos
```

**Ejecución:**
```bash
python -m pytest tests/test_integrity.py
# O directamente con argumentos:
python tests/test_integrity.py --host 127.0.0.1 --user root --password pwd --database db
```

---

## Flujo Completo de Trabajo

### Escenario típico de uso:

```bash
# 1. Preparar archivos CSV en data/db_input/
#    (copiar o actualizar archivos)

# 2. Ejecutar carga principal
python -m 02_database_connections \
  --host 127.0.0.1 \
  --user root \
  --password password123 \
  --database mi_base_datos

# 3. Verificar sincronización
python tests/test_table_names.py \
  --host 127.0.0.1 \
  --user root \
  --password password123 \
  --database mi_base_datos

# 4. Validar integridad de datos
python tests/test_integrity.py \
  --host 127.0.0.1 \
  --user root \
  --password password123 \
  --database mi_base_datos

# 5. Si todo está sincronizado ✅ = fin
#    Si hay inconsistencias ⚠️ 📂 = investigar
```

---

## Configuración Avanzada

### Consideraciones de Seguridad

1. **Contraseñas**: No pasar contraseñas en línea de comandos en producción
   - Usar variables de entorno: `$DB_PASSWORD`
   - O usar archivos de configuración encriptados

2. **Permisos MySQL**: Crear usuario con permisos limitados
   ```sql
   CREATE USER 'datos_user'@'localhost' IDENTIFIED BY 'password';
   GRANT CREATE, DROP, INSERT, SELECT, UPDATE ON database_name.* TO 'datos_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

### Limitaciones y Consideraciones

| Aspecto | Limitación | Solución |
|---------|-----------|----------|
| Tipos de datos | Solo INT, FLOAT, TEXT | Usar SQLAlchemy + SQLTypes |
| Tamaño de CSV | Depende de memoria RAM | Procesar por chunks |
| Características | No soporta índices/relaciones | Crear esquema post-carga |
| Errores de carga | Detiene en primer error | Implementar rollback parcial |

---

## Requisitos Previos del Sistema

### MySQL Server

Asegúrate de que esté habilitada la opción `local_infile`:

```sql
-- Verificar estado
SHOW VARIABLES LIKE 'local_infile';

-- Habilitar (si es necesario)
SET GLOBAL local_infile = 1;
```

### Cliente MySQL

El usuario debe tener permisos:

```sql
GRANT FILE ON *.* TO 'usuario'@'localhost';
GRANT CREATE, INSERT ON database_name.* TO 'usuario'@'localhost';
```

---

## Troubleshooting

### Error: "Access denied for user"
- Verifica las credenciales (host, user, password)
- Asegúrate de que el usuario existe en MySQL

### Error: "LOAD DATA LOCAL INFILE access denied"
- Habilita `local_infile` en el servidor
- Verifica permisos `FILE` del usuario

### Error: "Table already exists"
- El script usa `CREATE TABLE IF NOT EXISTS`, así que no debería ocurrir
- Si ocurre, verifica los permisos de escritura

### Error: "No such file or directory"
- Verifica que la carpeta `data/db_input/` existe
- Asegúrate de estar en el directorio correcto

---

## Dependencias

- `mysql-connector-python`: Conexión a MySQL
- `pandas`: Lectura y procesamiento de CSV
- `numpy`: Manejo de datos numéricos
- `sqlalchemy`: ORM y abstracción de BD
- `python-dotenv`: Manejo de variables de entorno

