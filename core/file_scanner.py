from PyQt5.QtCore import QThread, pyqtSignal
import os
from .file_metadata import FileMetadata

class FileScanWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        files_by_date = {}
        total_files = sum([len(files) for _, _, files in os.walk(self.path)])
        processed_files = 0

        for root, _, files in os.walk(self.path):
            rel_path = os.path.relpath(root, self.path)
            if rel_path == '.':
                rel_path = ''

            for file in files:
                self.process_file(root, rel_path, file, files_by_date)
                processed_files += 1
                if processed_files % 100 == 0:
                    self.progress.emit(int(processed_files * 100 / total_files))

        self.finished.emit(files_by_date)

    def process_file(self, root: str, rel_path: str, file: str, files_by_date: dict):
        try:
            full_path = os.path.join(root, file)
            date = FileMetadata.get_file_date(full_path)
            year_month = f"{date.year}/{date.month:02d}"

            if year_month not in files_by_date:
                files_by_date[year_month] = {}

            if rel_path not in files_by_date[year_month]:
                files_by_date[year_month][rel_path] = []

            files_by_date[year_month][rel_path].append({
                'name': file,
                'path': full_path,
                'date': date
            })
        except Exception as e:
            print(f"Error processing {full_path}: {e}")

class FileScanManager:
    def scan_date_view(self, directory, progress_callback, finished_callback):
        
        thread = FileScanWorker(directory)
        thread.progress.connect(progress_callback)
        thread.finished.connect(finished_callback)
        thread.start()
        return thread