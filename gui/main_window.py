from PyQt5.QtWidgets import QMainWindow
from .widgets.file_organizer_widget import FileOrganizerWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Archivos")
        self.resize(1200, 600)
        self.file_organizer = FileOrganizerWidget()
        self.setCentralWidget(self.file_organizer)
