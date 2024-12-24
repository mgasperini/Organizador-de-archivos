import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, 
    QComboBox, QFileDialog, QListView, QStackedWidget, QProgressBar, QHBoxLayout
)
from PyQt5.QtCore import Qt, QDir, QThread, pyqtSignal, QModelIndex
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileSystemModel
import os
import datetime

class FileMetadata:
    @staticmethod
    def get_file_date(file_path):
        if file_path.lower().endswith(('.jpg', '.jpeg')):
            try:
                from PIL import Image, ExifTags
                with Image.open(file_path) as img:
                    exif = img.getexif()
                    if exif:
                        for tag_id in (36867, 306, 36868):  # DateTimeOriginal, DateTime, DateTimeDigitized
                            if tag_id in exif:
                                date_str = exif[tag_id]
                                try:
                                    return datetime.datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                                except ValueError:
                                    pass
            except Exception:
                pass
        return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

class ScanWorker(QThread):
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
                full_path = os.path.join(root, file)
                try:
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

                    processed_files += 1
                    if processed_files % 100 == 0:
                        self.progress.emit(int(processed_files * 100 / total_files))

                except Exception as e:
                    print(f"Error processing {full_path}: {e}")

        self.finished.emit(files_by_date)

class FileOrganizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_directory = QDir.homePath()
        self.initialize_models()

    def setup_ui(self):
        self.main_layout = QHBoxLayout(self)

        # Botones de funcionalidades
        self.function_buttons_layout = QVBoxLayout()
        self.function_buttons_layout.setAlignment(Qt.AlignTop)
        
        self.reorganize_button = QPushButton("Reorganizar Archivos")
        self.reorganize_button.clicked.connect(self.show_reorganize_view)
        self.function_buttons_layout.addWidget(self.reorganize_button)

        # Placeholder para futuros botones
        self.duplicates_button = QPushButton("Eliminar Duplicados")
        self.duplicates_button.setEnabled(False)  # Funcionalidad futura
        self.function_buttons_layout.addWidget(self.duplicates_button)

        self.main_layout.addLayout(self.function_buttons_layout)

        # Stack de vistas
        self.stack_widget = QStackedWidget()
        self.main_layout.addWidget(self.stack_widget)

        # Vista de reorganización de archivos
        self.reorganize_view = QWidget()
        self.reorganize_layout = QVBoxLayout(self.reorganize_view)

        self.select_folder_button = QPushButton("Seleccionar Carpeta")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.reorganize_layout.addWidget(self.select_folder_button)

        self.file_list = QListView()
        self.file_list.doubleClicked.connect(self.navigate_directory)
        self.reorganize_layout.addWidget(self.file_list)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.reorganize_layout.addWidget(self.progress_bar)

        self.stack_widget.addWidget(self.reorganize_view)

    def initialize_models(self):
        # Modelo de sistema de archivos
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(self.current_directory)
        self.file_list.setModel(self.fs_model)
        self.file_list.setRootIndex(self.fs_model.index(self.current_directory))

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta", self.current_directory)
        if folder:
            self.current_directory = folder
            self.file_list.setRootIndex(self.fs_model.index(self.current_directory))

    def navigate_directory(self, index: QModelIndex):
        if self.fs_model.isDir(index):
            new_path = self.fs_model.filePath(index)
            self.current_directory = new_path
            self.file_list.setRootIndex(self.fs_model.index(new_path))

    def show_reorganize_view(self):
        self.stack_widget.setCurrentWidget(self.reorganize_view)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Archivos")
        self.resize(1200, 600)

        self.file_organizer = FileOrganizerWidget()
        self.setCentralWidget(self.file_organizer)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
