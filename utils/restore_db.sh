#!/bin/bash

# -----------------------------------------------------------------------------
# Script de restore de base de datos MySQL
# Uso: ./restore_db.sh <DB_NAME>
#   - DB_NAME: nombre de la base de datos (argumento obligatorio)
# -----------------------------------------------------------------------------

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
else
    echo "✗ Error: No se encontró el archivo .env en $PROJECT_ROOT"
    exit 1
fi

if [ -z "$1" ]; then
    echo "✗ Error: Debe especificar el nombre de la base de datos como argumento"
    echo "Uso: $0 <DB_NAME>"
    exit 1
fi

DB_NAME="$1"

BACKUP_DIR="$PROJECT_ROOT/data/db_backups"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "✗ Error: El directorio de backups no existe: $BACKUP_DIR"
    exit 1
fi

mapfile -t BACKUP_FILES < <(ls -1t "$BACKUP_DIR"/*.sql.gz 2>/dev/null || true)

if [ ${#BACKUP_FILES[@]} -eq 0 ]; then
    echo "✗ Error: No se encontraron archivos de backup en $BACKUP_DIR"
    exit 1
fi

echo ""
echo "=============================================="
echo "       Seleccionar archivo de backup"
echo "=============================================="
echo ""

for i in "${!BACKUP_FILES[@]}"; do
    FILENAME=$(basename "${BACKUP_FILES[$i]}")
    echo "  [$((i+1))] $FILENAME"
done

echo ""
read -p "Seleccione el número del archivo: " selection

if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 1 ] || [ "$selection" -gt ${#BACKUP_FILES[@]} ]; then
    echo "✗ Selección inválida"
    exit 1
fi

SELECTED_FILE="${BACKUP_FILES[$((selection-1))]}"
SELECTED_FILENAME=$(basename "$SELECTED_FILE")

echo ""
echo "----------------------------------------------"
echo "         Confirmar restore"
echo "----------------------------------------------"
echo ""
echo "  Archivo de backup: $SELECTED_FILENAME"
echo "  Base de datos:     $DB_NAME"
echo ""
read -p "¿Confirmar restore? (s/n): " confirm

if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    echo "Operación cancelada."
    exit 0
fi

echo ""
echo "Restaurando '$DB_NAME' desde '$SELECTED_FILENAME'..."

mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" -P"$DB_PORT" -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`"

gunzip < "$SELECTED_FILE" | mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" -P"$DB_PORT" "$DB_NAME"

if [ $? -eq 0 ]; then
    echo "✓ Restore completado exitosamente"
else
    echo "✗ Error al restaurar la base de datos"
    exit 1
fi
