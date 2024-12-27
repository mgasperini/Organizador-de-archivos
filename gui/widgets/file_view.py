from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListView, QFileDialog
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QFileSystemModel
import os

class FileView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.initialize_model()

        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.file_list = QListView()
        layout.addWidget(self.file_list)
        
    def initialize_model(self):
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(QDir.homePath())
        self.file_list.setModel(self.fs_model)
        self.file_list.setRootIndex(self.fs_model.index(QDir.homePath()))

    def select_folder(self, current_directory):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta", current_directory)
        if folder:
            self.file_list.setRootIndex(self.fs_model.index(folder))
            return folder
        return None

    def navigate_directory(self, index):
        if self.fs_model.isDir(index):
            new_path = self.fs_model.filePath(index)
            self.file_list.setRootIndex(self.fs_model.index(new_path))
            return new_path
        return None

    def go_up_directory(self, current_directory):
        new_path = os.path.dirname(current_directory)
        if os.path.exists(new_path):
            self.file_list.setRootIndex(self.fs_model.index(new_path))
            return new_path
        return None

    def set_current_directory(self, directory):
        self.file_list.setRootIndex(self.fs_model.index(directory))
