# CSV MySQL Connector

Una herramienta en Python para automatizar la carga de datos desde archivos CSV a una base de datos MySQL, incluyendo funcionalidades de creación automática de esquemas, validación de integridad de datos y control de sincronización entre archivos y tablas.

## Descripción General

Este proyecto proporciona dos utilidades principales:

1. **`main.py`**: Carga automática de datos CSV a MySQL con creación dinámica de tablas
2. **`table_names_control.py`**: Validación y control de sincronización entre archivos CSV y tablas de base de datos

## Estructura del Proyecto

```
02_database_connections/
├── src/
│   └── main.py                    # Script principal de carga
├── utils/
│   └── table_names_control.py     # Script de validación y control
├── data/                          # Carpeta de datos CSV
├── requirements.txt               # Dependencias
└── README.md                      # Este archivo
```

## Requisitos

- Python 3.8+ recomendado
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

## Uso General

### Paso 1: Preparar datos CSV

Coloca tus archivos CSV en la carpeta `data/` al nivel superior de `src`:

```
02_database_connections/
├── data/
│   ├── application_train.csv
│   ├── bureau.csv
│   └── ...
└── src/
```

**Requisitos del CSV:**
- Archivo debe tener extensión `.csv`
- Primera fila debe contener los nombres de las columnas (encabezados)
- Los valores deben estar separados por comas (`,`)
- Valores de texto deben estar entre comillas (`"`)

---

## 1. `main.py` - Script Principal de Carga

### Descripción

El script `main.py` automatiza el proceso completo de carga de datos CSV a MySQL:

1. **Conexión a la base de datos**: Se conecta al servidor MySQL
2. **Creación de base de datos**: Crea la BD si no existe
3. **Detección de archivos**: Busca todos los archivos `.csv` en la carpeta `data/`
4. **Creación automática de tablas**: Infiere tipos de datos y crea tablas
5. **Carga de datos**: Importa los datos usando `LOAD DATA LOCAL INFILE` (carga masiva optimizada)

### Funcionamiento Detallado

#### Paso 1: Configuración de Conexión
```bash
python src/main.py --host 127.0.0.1 --user root --password password123 --database mi_base_datos
```

- Crea la base de datos si no existe
- Establece la conexión y prepara el cursor

#### Paso 2: Procesamiento de Archivos CSV
Para cada archivo `.csv` en `data/`:

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
   ```sql
   CREATE TABLE IF NOT EXISTS `nombre_tabla` (
       `columna1` INT,
       `columna2` FLOAT,
       `columna3` TEXT,
       ...
   )
   ```

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

### Flujo de Ejecución

```
┌─────────────────────────────────────┐
│ Argumentos de línea de comandos     │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ Conectar a MySQL                    │
│ Crear BD si no existe               │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ Listar archivos CSV en data/        │
└────────────────┬────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
    Para cada CSV    No hay archivos
         │                │
         ▼                ▼
    ┌─────────────┐  Mostrar error
    │ Leer con    │
    │ Pandas      │
    └────┬────────┘
         │
         ▼
    ┌──────────────────┐
    │ Inferir tipos    │
    │ de datos         │
    └────┬─────────────┘
         │
         ▼
    ┌──────────────────┐
    │ Crear tabla      │
    │ en MySQL         │
    └────┬─────────────┘
         │
         ▼
    ┌──────────────────┐
    │ TRUNCATE         │
    │ (limpiar datos)  │
    └────┬─────────────┘
         │
         ▼
    ┌──────────────────────────┐
    │ LOAD DATA LOCAL INFILE   │
    │ (carga masiva)           │
    └────┬─────────────────────┘
         │
         ▼
    ┌──────────────────┐
    │ COMMIT           │
    │ (confirmar)      │
    └──────────────────┘
```

### Ejemplo de Uso

```bash
# Conexión a servidor local
python src/main.py \
  --host 127.0.0.1 \
  --user root \
  --password tu_password \
  --database datos_normalizados

# Salida esperada:
# Base de datos 'datos_normalizados' lista.
# Procesando application_train.csv...
# Tabla 'application_train' cargada exitosamente.
# Procesando bureau.csv...
# Tabla 'bureau' cargada exitosamente.
# ...
```

### Notas Importantes

1. **`LOAD DATA LOCAL INFILE` habilitado**: El script establece `allow_local_infile=True` en la conexión
2. **Permisos del servidor**: Asegúrate de que tu servidor MySQL permite `local_infile`
3. **Truncado automático**: Las tablas se vacían antes de cargar (reemplaza datos anteriores)
4. **Tipos de datos simplificados**: Solo usa INT, FLOAT y TEXT (considera SQLAlchemy para mayor flexibilidad)

---

## 2. `table_names_control.py` - Validación de Sincronización

### Descripción

Este script valida la sincronización entre los archivos CSV disponibles y las tablas existentes en la base de datos MySQL. Útil para:

- Verificar que todos los CSVs tienen tablas correspondientes
- Detectar archivos CSV que aún no se han cargado
- Encontrar tablas huérfanas (sin archivo CSV de origen)
- Auditoría de datos

### Funcionamiento Detallado

#### Paso 1: Conexión a la Base de Datos
```bash
python utils/table_names_control.py \
  --host 127.0.0.1 \
  --user root \
  --password password123 \
  --database mi_base_datos
```

#### Paso 2: Extracción de Nombres

**De la base de datos:**
- Ejecuta `SHOW TABLES` para obtener todas las tablas
- Almacena los nombres en un conjunto (`set`)

**De la carpeta `data/`:**
- Busca archivos con extensión `.csv`
- Extrae el nombre sin la extensión
- Almacena en un conjunto

#### Paso 3: Análisis Comparativo

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

#### Paso 4: Reporte

Genera un reporte categorizado mostrando:

```
┌─ RESUMEN DE COMPARACIÓN
├─ ✅ Coincidencias (n)
│  ├─ application_train
│  ├─ bureau
│  └─ ...
├─ ⚠️ Tablas en DB sin archivo CSV (n)
│  ├─ tabla_antigua
│  └─ ...
└─ 📂 Archivos CSV sin tabla en DB (n)
   ├─ nuevo_archivo.csv
   └─ ...
```

### Argumentos

Mismos que `main.py`:

| Argumento | Requerido | Descripción |
|-----------|-----------|-------------|
| `--host` | Sí | Dirección del servidor MySQL |
| `--user` | Sí | Usuario de MySQL |
| `--password` | Sí | Contraseña del usuario |
| `--database` | Sí | Nombre de la base de datos a verificar |

### Flujo de Ejecución

```
┌────────────────────────────────┐
│ Conectar a MySQL               │
│ Seleccionar BD                 │
└────────────┬───────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
 ┌─────────┐   ┌──────────────┐
 │ SHOW    │   │ Listar CSV   │
 │ TABLES  │   │ en data/     │
 └────┬────┘   └──────┬───────┘
      │               │
      ▼               ▼
 ┌──────────────────────────┐
 │ Comparar conjuntos       │
 │ - Coincidencias          │
 │ - Solo en BD             │
 │ - Solo en carpeta        │
 └────┬─────────────────────┘
      │
      ▼
 ┌──────────────────────────┐
 │ Mostrar reporte          │
 │ categorizado             │
 └──────────────────────────┘
```

### Ejemplo de Uso

```bash
python utils/table_names_control.py \
  --host 127.0.0.1 \
  --user root \
  --password password123 \
  --database datos_normalizados
```

### Salida Esperada

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

### Casos de Uso

**Caso 1: Verificación post-carga**
```bash
# Después de ejecutar main.py, verificar que todo se cargó correctamente
python utils/table_names_control.py --host 127.0.0.1 --user root --password pwd --database db
```

**Caso 2: Detección de datos huérfanos**
```
Si ves tablas en "⚠️ Tablas en DB sin archivo CSV", significa que:
- Alguien creó una tabla manualmente
- O se eliminó un CSV pero la tabla quedó en la BD
→ Acción: Considerar eliminar la tabla o buscar el CSV
```

**Caso 3: Carga incompleta**
```
Si ves archivos en "📂 Archivos CSV sin tabla en DB", significa que:
- Hay archivos nuevos que no se han cargado
→ Acción: Ejecutar main.py nuevamente
```

---

## Flujo Completo de Trabajo

### Escenario típico de uso:

```bash
# 1. Preparar archivos CSV en data/
#    (copiar o actualizar archivos)

# 2. Ejecutar carga principal
python src/main.py \
  --host 127.0.0.1 \
  --user root \
  --password password123 \
  --database mi_base_datos

# 3. Verificar sincronización
python utils/table_names_control.py \
  --host 127.0.0.1 \
  --user root \
  --password password123 \
  --database mi_base_datos

# 4. Si todo está sincronizado ✅ = fin
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
- Verifica que la carpeta `data/` existe
- Asegúrate de estar en el directorio correcto

---

## Dependencias

- `mysql-connector-python`: Conexión a MySQL
- `pandas`: Lectura y procesamiento de CSV
- `numpy`: Manejo de datos numéricos

NOTA: En un entorno de producción se recomienda SQLAlchemy para esta parte
