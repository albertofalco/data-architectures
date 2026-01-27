# CSV MySQL Connector

Una herramienta sencilla en Python para automatizar la carga de archivos CSV a una base de datos MySQL. El script detecta los archivos en la carpeta `data`, crea la base de datos y las tablas si no existen, e importa los datos.

## Estructura del proyecto
- `src/main.py`: Script principal de procesamiento.
- `data/`: Carpeta donde se deben colocar los archivos `.csv` (está al mismo nivel que `src`).
- `requirements.txt`: Dependencias necesarias para ejecutar el script.

## Requisitos
- Python 3.8+ recomendado
- Acceso a un servidor MySQL

## Instalación (sin **setup.py** / **pyproject**)

1. Clona o descarga este repositorio.
2. Crea y activa un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instala las dependencias desde `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Uso

Ejecuta directamente el script `main.py` pasando los argumentos de conexión:

```bash
python src/main.py --host 127.0.0.1 --user tu_usuario --password tu_password --database nombre_db
```

Notas:
- Coloca tus archivos CSV en la carpeta `data/` (ubicada al nivel superior de `src`).
- El script usa `LOAD DATA LOCAL INFILE`; asegúrate de que el cliente/servidor MySQL permitan `local_infile` si usas esa ruta.
- Si prefieres evitar `LOAD DATA LOCAL INFILE`, puedes modificar `src/main.py` para insertar filas con Pandas/SQLAlchemy.

## Argumentos del script

- `--host`: Dirección del servidor MySQL.
- `--user`: Usuario de la base de datos.
- `--password`: Contraseña del usuario.
- `--database`: Nombre de la base de datos (se creará si no existe).
