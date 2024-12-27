from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, 
    QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QDir
from .navigation_bar import NavigationBar, ViewMode
from .file_view import FileView
from .date_view import DateView
from .duplicates_view import DuplicatesView
from .sidebar import Sidebar
from core.file_scanner import FileScanWorker
from core.file_organizer import FileOrganizer
from core.file_hash_scanner import FileHashScanWorker

class FileOrganizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_directory = QDir.homePath()
        self.history = []
        self.history_index = -1
        self.actual_view = None
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
        self.duplicates_view = DuplicatesView(self)

        self.actual_view = self.file_view
        
        self.stack_widget.addWidget(self.file_view)
        self.stack_widget.addWidget(self.date_view)
        self.stack_widget.addWidget(self.duplicates_view)
        
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
        self.navigation_bar.file_view_button.clicked.connect(self.toggle_date_view)
        self.navigation_bar.to_original_button.clicked.connect(self.reorganize_to_original)
        self.navigation_bar.order_by_date_button.clicked.connect(self.reorganize_files)
        self.navigation_bar.duplicates_button.clicked.connect(self.show_duplicate_view)

        # Sidebar connections
        self.sidebar.reorganize_button.clicked.connect(self.toggle_date_view)
        self.sidebar.duplicates_button.clicked.connect(self.show_duplicate_view)
        
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
        self.actual_view = self.file_view
        self.navigation_bar.update_view(view_mode=ViewMode.NORMAL)
        self.current_directory = QDir.homePath()
        self.file_view.set_current_directory(self.current_directory)
        self.stack_widget.setCurrentWidget(self.file_view)
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
        else:
            self.stack_widget.setCurrentWidget(self.file_view)
            self.actual_view = self.file_view
            self.navigation_bar.update_view(view_mode=ViewMode.NORMAL)

    def show_date_view(self):
        self.actual_view = self.date_view
        self.navigation_bar.update_view(view_mode=ViewMode.DATE)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        # Limpiar thread anterior si existe
        if hasattr(self, 'scan_thread') and self.scan_thread is not None:
            if self.scan_thread.isRunning():
                self.scan_thread.wait()  # Esperar a que termine
        
        self.scan_thread = FileScanWorker(self.current_directory)
        self.scan_thread.progress.connect(self.progress_bar.setValue)
        self.scan_thread.finished.connect(self.populate_date_view)
        self.scan_thread.start()

    def populate_date_view(self, files_by_date):
        self.date_view.populate_tree(files_by_date)
        self.progress_bar.setVisible(False)
        self.stack_widget.setCurrentWidget(self.date_view)

    def reorganize_files(self):
        if self.stack_widget.currentWidget() == self.file_view:
                self.toggle_date_view()
 

        if FileOrganizer.contains_date(self.current_directory):
            msg_box_warning = QMessageBox(self)
            msg_box_warning.setWindowTitle("Advertencia")
            msg_box_warning.setText("La carpeta ya tiene una estructura de fecha. ¿Desea continuar con la reorganización?")
            msg_box_warning.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box_warning.button(QMessageBox.Yes).setText("Sí")

             # Si el usuario selecciona No, cancelar la operación
            if msg_box_warning.exec() == QMessageBox.No:
                return  
            
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar reorganización")
        msg_box.setText("Se modificarán los archivos del sistema. ¿Está seguro de continuar?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.button(QMessageBox.Yes).setText("Sí")

            
        if msg_box.exec() == QMessageBox.Yes:
            # Limpiar thread anterior si existe
            if hasattr(self, 'scan_thread') and self.scan_thread is not None:
                if self.scan_thread.isRunning():
                    self.scan_thread.wait()  # Esperar a que termine
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
            self.stack_widget.setCurrentWidget(self.file_view)  # Actualizar la vista


    def show_duplicate_view(self):
        self.actual_view = self.duplicates_view
        self.current_directory = self.history[-1]
        self.navigation_bar.update_view(view_mode=ViewMode.DUPLICATES)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Limpiar thread anterior si existe
        if hasattr(self, 'hash_scan_thread') and self.hash_scan_thread is not None:
            if self.hash_scan_thread.isRunning():
                self.hash_scan_thread.wait()  # Esperar a que termine
        
        self.hash_scan_thread = FileHashScanWorker(self.current_directory)
        self.hash_scan_thread.progress.connect(self.progress_bar.setValue)
        self.hash_scan_thread.finished.connect(self.populate_duplicate_view)
        self.hash_scan_thread.start()

    def populate_duplicate_view(self, duplicate_files):
        self.duplicates_view.populate_table(duplicate_files)
        self.progress_bar.setVisible(False)
        self.stack_widget.setCurrentWidget(self.duplicates_view)
