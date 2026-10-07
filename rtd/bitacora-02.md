# Bitácora 2: Configuración de entorno e importación de datos

## Objetivo

Esta bitácora describe la preparación del entorno necesario para automatizar la importación y gestión de datos en MySQL, incluyendo la creación de un usuario específico para la conexión mediante Python, la configuración del entorno virtual y la asignación de los privilegios requeridos para los distintos usuarios de la base de datos. 

## Preparación de herramientas y gestión de usuarios

Se preparan las herramientas y variables necesarias para la importación de las tablas a la base de datos. Se utiliza MySQL Workbench con el usuario `admin` para crear un nuevo usuario destinado a la automatización.

- Usuario: `db-python-user`
- Servidor: `localhost`

## Configuración del entorno virtual (Python)

Para garantizar el encapsulamiento de las librerías y evitar conflictos de dependencias, se configura un entorno virtual.

```bash
# Instalación de la herramienta virtual env para Python 3.12
sudo apt install python3.12-venv

# Crear el entorno virtual en la carpeta 'venv'
python3 -m venv venv

# Activar el entorno (Linux/Mac)
source venv/bin/activate
```

## Configuración de privilegios

Se establecen los permisos definitivos para los usuarios en el servidor MySQL para permitir la gestión y carga de datos.

- Usuario `admin`: Se le asigna rol de DBA (Administrador de Base de Datos).
- Usuario `db-python-user`: Se le asigna rol de DB Manager con permisos más limitados frente al usuario anterior.
