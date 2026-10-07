# Bitácora 1: Instalación y configuración de MySQL

## Instalación del servidor MySQL y acceso

Se instala MySQL Community Server en el entorno de Linux 64 Bits. Se accede como usuario `root` al servidor MySQL:

```bash
sudo mysql
```

## Listado de bases de datos y usuarios

Se obtiene el listado de todas las bases de datos alojadas en el servidor y todos los usuarios registrados por defecto.

```sql
SHOW DATABASES;
SELECT user FROM mysql.user;
```

## Creación de usuarios y verificación de permisos

Se crea un usuario `admin` en el entorno local (`localhost`). Se le otorgan permisos de creación y modificación a nivel general en el servidor MySQL y la opción de conceder permisos a otros usuarios.

```sql
CREATE USER 'admin'@'localhost' IDENTIFIED BY '**********';

GRANT CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, SELECT, REFERENCES,
RELOAD ON *.* TO 'admin'@'localhost' WITH GRANT OPTION;
```

Se consultan nuevamente los usuarios vigentes y los privilegios asignados al usuario `admin`:

```sql
SELECT user FROM mysql.user;
SHOW GRANTS FOR 'admin'@'localhost';
```

## Configuración de MySQL Workbench

Se inicializa el entorno MySQL Workbench y se crea una conexión para el usuario `admin` en el entorno local. Se verifica que el usuario `admin` puede visualizar las bases de datos disponibles:

```sql
SHOW DATABASES;
```

## Creación de bases de datos de trabajo

Se crearon las bases de datos `data_arch_prod` y `data_arch_test` en el entorno local y se confirma su creación listando las bases disponibles.

```sql
CREATE DATABASE data_arch_prod;
CREATE DATABASE data_arch_test;
SHOW DATABASES;
```
