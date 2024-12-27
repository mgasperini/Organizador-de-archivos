from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, 
    QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QDir
from .navigation_bar import NavigationBar
from .file_view import FileView
from .date_view import DateView
from .sidebar import Sidebar
from core.file_scanner import FileScanWorker
from core.file_organizer import FileOrganizer

class FileOrganizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_directory = QDir.homePath()
        self.history = []
        self.history_index = -1
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        
        # Sidebar
        self.sidebar = Sidebar(self)
        self.main_layout.addWidget(self.sidebar)
        
        # Content area
        self.content_layout = QVBoxLayout()
        
        # Navigation bar
        self.navigation_bar = NavigationBar(self)
        self.content_layout.addWidget(self.navigation_bar)
        
        # Stack widget for views
        self.stack_widget = QStackedWidget()
        self.file_view = FileView(self)
        self.date_view = DateView(self)
        
        self.stack_widget.addWidget(self.file_view)
        self.stack_widget.addWidget(self.date_view)
        
        self.content_layout.addWidget(self.stack_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.content_layout.addWidget(self.progress_bar)
        
        self.main_layout.addLayout(self.content_layout)

    def setup_connections(self):
        # Navigation connections
        self.navigation_bar.home_button.clicked.connect(self.navigate_home)
        self.navigation_bar.back_button.clicked.connect(self.navigate_back)
        self.navigation_bar.forward_button.clicked.connect(self.navigate_forward)
        self.navigation_bar.up_button.clicked.connect(self.go_up_directory)
        self.navigation_bar.select_folder_button.clicked.connect(self.select_folder)
        self.navigation_bar.date_view_button.clicked.connect(self.toggle_date_view)
        self.navigation_bar.to_original_button.clicked.connect(self.reorganize_to_original)

        # Sidebar connections
        self.sidebar.reorganize_button.clicked.connect(self.reorganize_files)
        
        # File view connections
        self.file_view.file_list.doubleClicked.connect(self.navigate_directory)

    def select_folder(self):
        new_folder = self.file_view.select_folder(self.current_directory)
        if new_folder:
            self.current_directory = new_folder
            self.update_history(new_folder)

    def navigate_directory(self, index):
        new_path = self.file_view.navigate_directory(index)
        if new_path:
            self.current_directory = new_path
            self.update_history(new_path)

    def go_up_directory(self):
        new_path = self.file_view.go_up_directory(self.current_directory)
        if new_path:
            self.current_directory = new_path
            self.update_history(new_path)

    def navigate_home(self):
        self.current_directory = QDir.homePath()
        self.file_view.set_current_directory(self.current_directory)
        self.update_history(self.current_directory)

    def navigate_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_directory = self.history[self.history_index]
            self.file_view.set_current_directory(self.current_directory)

    def navigate_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_directory = self.history[self.history_index]
            self.file_view.set_current_directory(self.current_directory)

    def update_history(self, new_path):
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(new_path)
        self.history_index = len(self.history) - 1

    def toggle_date_view(self):
        if self.stack_widget.currentWidget() == self.file_view:
            self.show_date_view()
            self.navigation_bar.date_view_button.setText("Ver Vista Actual")
        else:
            self.stack_widget.setCurrentWidget(self.file_view)
            self.navigation_bar.date_view_button.setText("Ver por Fechas")

    def show_date_view(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.scan_thread = FileScanWorker(self.current_directory)
        self.scan_thread.progress.connect(self.progress_bar.setValue)
        self.scan_thread.finished.connect(self.populate_date_view)
        self.scan_thread.start()

    def populate_date_view(self, files_by_date):
        self.date_view.populate_tree(files_by_date)
        self.progress_bar.setVisible(False)
        self.stack_widget.setCurrentWidget(self.date_view)

    def reorganize_files(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar reorganización")
        msg_box.setText("Se modificarán los archivos del sistema. ¿Está seguro de continuar?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.button(QMessageBox.Yes).setText("Sí")
        
        if msg_box.exec() == QMessageBox.Yes:
            FileOrganizer.reorganize_by_date(
                self.date_view.get_files_by_date(),
                self.current_directory
            )
            self.show_date_view()  # Actualizar la vista

    def reorganize_to_original(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar deshacer reorganización")
        msg_box.setText("Se reorganizarán los archivos al directorio original. ¿Está seguro de continuar?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.button(QMessageBox.Yes).setText("Sí")
        
        if msg_box.exec() == QMessageBox.Yes:
            FileOrganizer.restore_original_structure(self.current_directory)
            QMessageBox.information(self, "Proceso Completo", 
                                  "Los archivos han sido reorganizados a sus carpetas originales.")
            self.show_date_view()  # Actualizar la vista
