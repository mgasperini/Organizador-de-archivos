import os
import shutil
import re
from typing import Dict, List

class FileOrganizer:
    MONTH_NAMES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    @staticmethod
    def reorganize_by_date(files_by_date: Dict, base_path: str):
        """
        Reorganiza los archivos según su fecha en una estructura de carpetas año/mes.
        """
        for year_month, directories in files_by_date.items():
            year, month = map(int, year_month.split('/'))
            month_name = FileOrganizer.MONTH_NAMES[month - 1]
            
            for directory, files in directories.items():
                target_folder = os.path.join(
                    base_path, 
                    str(year), 
                    f"{month:02d}-{month_name}"
                )
                
                if directory:
                    target_folder = os.path.join(target_folder, directory)

                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)
                
                for file_info in files:
                    try:
                        shutil.move(file_info['path'], target_folder)
                    except Exception as e:
                        print(f"Error moving {file_info['path']}: {e}")

            # Limpiar carpetas vacías
            FileOrganizer._clean_empty_directories(base_path)

    @staticmethod
    def restore_original_structure(base_path: str):
        """
        Restaura la estructura original de los archivos.
        """
        date_pattern = r'(?:(\d{4}\\\d{2}-(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|' \
                      r'Septiembre|Octubre|Noviembre|Diciembre))|(\d{2}\\\d{2}\\)|' \
                      r'(\d{2}\\(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|' \
                      r'Septiembre|Octubre|Noviembre|Diciembre))|(\d{4}\\(Enero|Febrero|' \
                      r'Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|' \
                      r'Diciembre)))(\\.+)$'

        folder_map = {}
        files_without_subfolder = []

        for root, _, files in os.walk(base_path):
            for file in files:
                relative_path = os.path.relpath(root, base_path)
                file_path = os.path.join(root, file)

                # Verificar si el archivo está en una estructura de fecha
                match = re.search(date_pattern, relative_path)
                
                if match:
                    if os.sep in relative_path:  # Tiene una subcarpeta
                        subfolder_name = os.path.basename(root)
                        if subfolder_name not in folder_map:
                            folder_map[subfolder_name] = []
                        folder_map[subfolder_name].append(file_path)
                else:
                    files_without_subfolder.append(file_path)

        # Mover archivos a sus ubicaciones originales
        FileOrganizer._move_files_to_original_locations(
            base_path, 
            folder_map, 
            files_without_subfolder
        )

    @staticmethod
    def _move_files_to_original_locations(
        base_path: str, 
        folder_map: Dict[str, List[str]], 
        files_without_subfolder: List[str]
    ):
        """
        Mueve los archivos a sus ubicaciones originales.
        """
        # Mover archivos sin subcarpeta
        for file_path in files_without_subfolder:
            try:
                shutil.move(file_path, base_path)
            except Exception as e:
                print(f"Error moving {file_path}: {e}")

        # Mover archivos con subcarpeta
        for subfolder, files in folder_map.items():
            target_folder = os.path.join(base_path, subfolder)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            
            for file_path in files:
                try:
                    shutil.move(file_path, target_folder)
                except Exception as e:
                    print(f"Error moving {file_path}: {e}")

        # Limpiar carpetas vacías
        FileOrganizer._clean_empty_directories(base_path)

    @staticmethod
    def _clean_empty_directories(path: str):
        """
        Elimina recursivamente las carpetas vacías.
        """
        for root, dirs, files in os.walk(path, topdown=False):
            if not os.listdir(root) and root != path:
                try:
                    os.rmdir(root)
                except Exception as e:
                    print(f"Error removing empty directory {root}: {e}")
