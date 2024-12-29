from PyQt5.QtWidgets import QMainWindow
from .widgets.file_organizer_widget import FileOrganizerWidget
from gui.widgets.navigation_bar import NavigationBar
from core.navigation_controller import NavigationController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Archivos")
        self.resize(1200, 600)
        self.file_organizer = FileOrganizerWidget()
        self.setCentralWidget(self.file_organizer)

    def setup_navigation(self):
        self.navigation_bar = NavigationBar(self)
        self.navigation_controller = NavigationController(
            self.navigation_bar,
            self.file_organizer
        )