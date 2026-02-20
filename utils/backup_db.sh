#!/bin/bash

# -----------------------------------------------------------------------------
# Script de backup de base de datos MySQL
# Uso: ./backup_db.sh [DB_NAME]
#   - Sin argumentos: usa DB_NAME del archivo .env
#   - Con argumento: usa el nombre de DB proporcionado
# -----------------------------------------------------------------------------

set -e

# Obtener la ruta del script y del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Cargar variables de entorno desde .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
else
    echo "✗ Error: No se encontró el archivo .env en $PROJECT_ROOT"
    exit 1
fi

# Usar DB_NAME del argumento o del .env (prioridad al argumento)
DB_NAME="${1:-$DB_NAME}"

# Validar que se tenga el nombre de la base de datos
if [ -z "$DB_NAME" ]; then
    echo "✗ Error: No se especificó DB_NAME (ni como argumento ni en .env)"
    exit 1
fi

# Definir directorio de backups y crearlo si no existe
BACKUP_DIR="$PROJECT_ROOT/data/db_backups"
mkdir -p "$BACKUP_DIR"

# Generar nombre de archivo con timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="${DB_NAME}_${TIMESTAMP}.sql.gz"
FILEPATH="$BACKUP_DIR/$FILENAME"

# Verificar si el archivo ya existe y confirmar reemplazo
if [ -f "$FILEPATH" ]; then
    read -p "El archivo $FILENAME ya existe. ¿Sobrescribir? (s/n): " confirm
    if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
        echo "Operación cancelada."
        exit 0
    fi
fi

echo "Creando backup de '$DB_NAME'..."

# Ejecutar mysqldump y comprimir con gzip
mysqldump -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" -P"$DB_PORT" "$DB_NAME" | gzip > "$FILEPATH"

# Verificar que el backup se creó correctamente
if [ $? -eq 0 ] && [ -f "$FILEPATH" ]; then
    echo "✓ Backup creado exitosamente: $FILEPATH"
else
    echo "✗ Error al crear el backup"
    [ -f "$FILEPATH" ] && rm -f "$FILEPATH"
    exit 1
fi
