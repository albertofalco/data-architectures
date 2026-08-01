"""Download Google Drive assets and protect them through the project .gitignore."""

# ==================== IMPORTS ====================

import gdown
import zipfile
import argparse
import os
from pathlib import Path


# ==================== HELPER FUNCTIONS ====================


def is_folder_populated(path):
    """Return whether a directory exists and contains at least one entry."""
    return path.exists() and any(path.iterdir())


def update_gitignore(path_to_ignore):
    """Add a normalized download path to the project .gitignore."""
    # Locate the repository .gitignore one level above utils.
    gitignore_path = Path(__file__).parent.parent / ".gitignore"
    
    # Normalize the path relative to the repository root.
    # Example: './data/raw' becomes 'data/raw/'.
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
    """Download a Google Drive asset and extract it when it is a ZIP archive."""
    destination = Path(dest_path)
    
    # 1. Protect the destination from accidental commits.
    update_gitignore(dest_path)
    
    # 2. Skip downloads when the destination is already populated.
    if is_folder_populated(destination):
        print(f"La ruta '{destination}' ya contiene archivos. Saltando descarga.")
        return

    destination.mkdir(parents=True, exist_ok=True)
    url = f'https://drive.google.com/uc?id={file_id}'
    
    print(f"Iniciando descarga en: {destination}")
    
    # Download to a temporary filename before determining the asset type.
    temp_name = "temp_download"
    downloaded_file = gdown.download(url, quiet=False, fuzzy=True, output=str(destination / temp_name))
    
    if not downloaded_file:
        print("Error: No se pudo completar la descarga.")
        return

    downloaded_path = Path(downloaded_file)

    # 3. Extract ZIP archives and remove their temporary download.
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


# ==================== EXECUTION ====================


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descarga assets y actualiza .gitignore.")
    parser.add_argument("id", help="ID del archivo en Google Drive")
    parser.add_argument("dest", help="Ruta de destino")

    args = parser.parse_args()
    download_and_setup(args.id, args.dest)
