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

- Python 3.8+.
- Acceso a un servidor MySQL (local o remoto).
- Servidor MySQL con permisos de creación de bases de datos.
- Dependiendo de la librería utilizada, puede suceder que sea necesario habilitar la opción `local_infile` en MySQL:

```sql
-- Verificar estado
SHOW VARIABLES LIKE 'local_infile';

-- Habilitar (si es necesario)
SET GLOBAL local_infile = 1;
```

- El usuario debe tener permisos para crear e insertar datos en la base de datos.
- Librerias necesarias:
  - `mysql-connector-python`: Conexión a MySQL
  - `pandas`: Lectura y procesamiento de CSV
  - `numpy`: Manejo de datos numéricos
  - `sqlalchemy`: ORM y abstracción de BD
  - `python-dotenv`: Manejo de variables de entorno

## Instalación

1. Clona o descarga este repositorio.
2. Crea y activa un entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Instala las dependencias:

```bash
pip install -r 02_database_connections/requirements.txt
```

## Configuración

### Preparación de Datos

Colocar los archivos CSV en la carpeta `data/db_input/`:

```
02_database_connections/
...
data/
└── db_input/
    ├── application_train.csv
    ├── bureau.csv
    └── ...
```

**Requisitos del CSV:**
- Archivo debe tener extensión `.csv`
- Primera fila debe contener los nombres de las columnas (encabezados)
- Los valores deben estar separados por comas (`,`)
- Valores de texto deben estar entre comillas (`"`)

## Funcionamiento del script principal: `src/__main__.py`

### Descripción

Automatiza el proceso completo de carga de datos CSV a MySQL:

1. **Conexión a la base de datos**: Se conecta al servidor MySQL.
2. **Creación de base de datos**: Crea la BD si no existe.
3. **Detección de archivos**: Busca todos los archivos `.csv` en la carpeta `data/db_input/`.
4. **Creación automática de tablas**: Infiere tipos de datos y crea tablas.

### Configuración de Conexión

El script obtiene los datos y credenciales de acceso a la base de datos del archivo .env ubicado en la raiz del repositorio.

```
01_data_normalization/
02_database_connections/
data/
...
.env
```

El archivo .env contiene la siguiente estructura:

```bash
DB_HOST=localhost
DB_USER=user
DB_PASSWORD=password
DB_NAME=example
```

El script también admite la inserción de argumentos en la terminal para ejecutarlo.

```bash
# python -m 02_database_connections --host localhost --user user --password password --database example
```

Una vez configurada la conexión al servidor MySQL, crea la base de datos DB_NAME si no existe.

### Procesamiento de Archivos CSV con SQLAlchemy

Para cada archivo `.csv` en `data/db_input/`, se realiza la lectura con la librería **Pandas** y el motor **SQLAlchemy**.

El proceso de importación a la base de datos:
   - Analiza el tipo de datos de cada columna.
   - Gestiona y convierte a formato compatible los valores `np.nan` y `None` a `NULL`.
   - Crea la tabla si no existe.
   - Borra los registros anteriores si la tabla ya existe (TRUNCATE).
   - Ignora la primera fila (headers).

### Ejemplo de Uso

```bash
python -m 02_database_connections
```

---

## Tests

El módulo incluye tres suites de tests para validar diferentes aspectos de la conexión y carga de datos.

### test_db_connection.py

Verifica la conectividad a la base de datos usando dos métodos diferentes:

- `mysql-connector-python`: Conexión nativa a MySQL.
- `SQLAlchemy`: ORM con driver MySQL.

**Ejecución:**
```bash
python -m tests.test_db_connection
# Opcion alternativa:
python tests/test_db_connection.py
```

### test_table_names.py

Valida la sincronización entre los archivos CSV disponibles y las tablas existentes en la base de datos MySQL:
- Verifica que todos los CSVs tienen tablas correspondientes.
- Detecta archivos CSV que aún no se han cargado.
- Encuentra tablas huérfanas (sin archivo CSV de origen).
- Auditoría de calidad de datos.

**Ejecución:**
```bash
python -m 02_database_connections.tests.test_table_names
# Opción alternativa (con argumentos):
python tests/test_table_names.py --host 127.0.0.1 --user user --password password --database example
```

### test_integrity.py

Control de contenido de tablas verificando integridad comparándolas con archivos fuente:
- **Validación de nombres de tablas**: Compara tablas en BD vs archivos CSV
- **Validación de estructura (shape)**: Verifica que filas y columnas coincidan
- **Validación de esquema**: Comprueba nombres y orden de columnas
- **Comparación de contenido**: Validación celda por celda con tolerancia en decimales

**Ejecución:**
```bash
python -m 02_database_connections.tests.test_integrity.py
# Opcion alternativa (con argumentos):
python 02_database_connections/tests/test_integrity.py --host 127.0.0.1 --user user --password password --database example
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

### Troubleshooting

#### Error: "Access denied for user"
- Verifica las credenciales (host, user, password).
- Asegúrate de que el usuario existe en MySQL.

#### Error: "LOAD DATA LOCAL INFILE access denied"
- Habilita `local_infile` en el servidor.
- Verifica permisos `FILE` del usuario.

#### Error: "Table already exists"
- El script usa `CREATE TABLE IF NOT EXISTS`, así que no debería ocurrir.
- Si ocurre, verifica los permisos de escritura.

#### Error: "No such file or directory"
- Verifica que la carpeta `data/db_input/` existe.
- Asegúrate de estar en el directorio correcto.

---


