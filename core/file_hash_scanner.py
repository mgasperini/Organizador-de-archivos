from PyQt5.QtCore import QThread, pyqtSignal
import os
import hashlib
from .file_metadata import FileMetadata

class FileHashScanWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)
    
    def __init__(self, path):
        super().__init__()
        self.path = path
        
    def calculate_file_hash(self, filepath: str, block_size=65536) -> str:
        """Calcula SHA-256 hash de los archivos."""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for block in iter(lambda: f.read(block_size), b""):
                    sha256_hash.update(block)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Error al calcular el hash del archivo {filepath}: {e}")
            return None

    def run(self):
        files_by_hash = {}  # Diccionario para agrupar los archivos por su hash
        duplicates = {}     # Diccionario para guardar solo los archivos duplicados
        
        # Total de archivos a procesar
        total_files = sum([len(files) for _, _, files in os.walk(self.path)])
        processed_files = 0
        
        # Procesa los archivos y calcula los hashes
        for root, _, files in os.walk(self.path):
            for file in files:
                full_path = os.path.join(root, file)
                file_hash = self.calculate_file_hash(full_path)
                
                if file_hash:
                    file_info = {
                        'name': file,
                        'path': full_path,
                        'size': os.path.getsize(full_path),
                        'date': FileMetadata.get_file_date(full_path)
                    }
                    
                    if file_hash in files_by_hash:
                        # If we find a duplicate, ensure it's in the duplicates dict
                        if file_hash not in duplicates:
                            duplicates[file_hash] = {
                                'files': [files_by_hash[file_hash]],
                                'size': file_info['size']
                            }
                        duplicates[file_hash]['files'].append(file_info)
                    else:
                        files_by_hash[file_hash] = file_info
                
                # Update progress
                processed_files += 1
                if processed_files % 100 == 0:
                    self.progress.emit(int(processed_files * 100 / total_files))
        self.finished.emit(duplicates)
