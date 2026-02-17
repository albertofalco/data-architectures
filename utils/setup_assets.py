"""
Script para descarga y configuración de assets desde Google Drive.

Este módulo proporciona funcionalidades para descargar archivos o carpetas
desde Google Drive, extraerlos si son archivos ZIP, y gestionar automáticamente
la protección de estos archivos en .gitignore para evitar subirlos al repositorio.

Uso:
    python setup_assets.py <file_id> <dest_path>

Ejemplo:
    python setup_assets.py 1BcxEuEUQyF5x34gwbMGeY9W1qW3h8hQw /ruta/destino
"""

import gdown
import zipfile
import argparse
import os
from pathlib import Path

def is_folder_populated(path):
    """
    Verifica si la carpeta existe y contiene archivos.
    
    Args:
        path: Objeto Path que representa la ruta a verificar.
    
    Returns:
        bool: True si la carpeta existe y contiene al menos un archivo o subcarpeta,
              False en caso contrario.
    """
    return path.exists() and any(path.iterdir())

def update_gitignore(path_to_ignore):
    """
    Añade la ruta de descarga al .gitignore de la raíz del proyecto.
    
    Busca el archivo .gitignore en el directorio raíz del repositorio y añade
    la ruta especificada si no está ya presente. Esto evita que los archivos
    descargados se suban accidentalmente al control de versiones.
    
    Args:
        path_to_ignore: Ruta relativa o absoluta que se desea proteger.
                       Se normalizará para ser relativa a la raíz del repo.
    """
    # Buscamos el .gitignore subiendo un nivel desde 'utils/'
    gitignore_path = Path(__file__).parent.parent / ".gitignore"
    
    # Normalizamos la ruta para que sea relativa a la raíz del repo
    # Ejemplo: './data/raw' -> 'data/raw/'
    clean_path = str(Path(path_to_ignore)).replace("\\", "/").strip("./").strip("/") + "/"
    
    if not gitignore_path.exists():
        print(f"Creando nuevo archivo .gitignore en {gitignore_path}")
        gitignore_path.write_text(f"{clean_path}\n", encoding="utf-8")
        return

    lines = gitignore_path.read_text(encoding="utf-8").splitlines()
    if clean_path not in lines:
        print(f"Añadiendo '{clean_path}' al .gitignore para evitar subidas accidentales.")
        with gitignore_path.open("a", encoding="utf-8") as f:
            f.write(f"\n# Assets descargados automáticamente\n{clean_path}\n")
    else:
        print(f"La ruta '{clean_path}' ya está protegida en .gitignore.")

def download_and_setup(file_id, dest_path):
    """
    Descarga un archivo desde Google Drive y lo configura en la ruta destino.
    
    Este proceso incluye:
    1. Añadir la ruta destino al .gitignore para protección
    2. Verificar si los archivos ya existen para evitar descargas duplicadas
    3. Descargar el archivo desde Google Drive usando gdown
    4. Extraer el contenido si es un archivo ZIP
    5. Limpiar archivos temporales de descarga
    
    Args:
        file_id: ID del archivo en Google Drive (extracted from the share URL).
        dest_path: Ruta destino donde se guardarán los archivos descargados.
    
    Returns:
        None. La función imprime mensajes de estado durante el proceso.
    """
    destination = Path(dest_path)
    
    # 1. Asegurar protección en Git
    update_gitignore(dest_path)
    
    # 2. Verificación de existencia
    if is_folder_populated(destination):
        print(f"La ruta '{destination}' ya contiene archivos. Saltando descarga.")
        return

    destination.mkdir(parents=True, exist_ok=True)
    url = f'https://drive.google.com/uc?id={file_id}'
    
    print(f"Iniciando descarga en: {destination}")
    
    # Descarga temporal
    temp_name = "temp_download"
    downloaded_file = gdown.download(url, quiet=False, fuzzy=True, output=str(destination / temp_name))
    
    if not downloaded_file:
        print("Error: No se pudo completar la descarga.")
        return

    downloaded_path = Path(downloaded_file)

    # 3. Procesamiento
    if downloaded_path.suffix.lower() == '.zip':
        print(f"Descomprimiendo ZIP en {destination}...")
        try:
            with zipfile.ZipFile(downloaded_path, 'r') as zip_ref:
                zip_ref.extractall(destination)
        finally:
            downloaded_path.unlink()
            print("Limpieza de temporal completada.")
    else:
        print(f"Archivo individual guardado en: {downloaded_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descarga assets y actualiza .gitignore.")
    parser.add_argument("id", help="ID del archivo en Google Drive")
    parser.add_argument("dest", help="Ruta de destino")

    args = parser.parse_args()
    download_and_setup(args.id, args.dest)