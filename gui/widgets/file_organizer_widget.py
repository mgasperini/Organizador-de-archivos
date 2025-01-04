from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, 
    QProgressBar, QMessageBox
)
from PyQt5.QtCore import QDir, pyqtSignal
from .navigation_bar import NavigationBar
from .file_view import FileView
from .date_view import DateView
from .duplicates_view import DuplicatesView
from .sidebar import Sidebar
from core.file_organizer import FileOrganizer
from core.theme_manager import ThemeManager
from core.navigation_controller import NavigationController


class FileOrganizerWidget(QWidget):
    view_changed = pyqtSignal(QWidget)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_directory = QDir.homePath()
        self.actual_view = None
        self.theme_manager = ThemeManager()
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        
        # Sidebar
        self.sidebar = Sidebar(self)
        self.main_layout.addWidget(self.sidebar)
        
        # Content area
        self.content_layout = QVBoxLayout()
        
        
        # Stack widget for views
        self.stack_widget = QStackedWidget()
        self.file_view = FileView(self)
        self.date_view = DateView(self)
        self.duplicates_view = DuplicatesView(self)

        self.actual_view = self.file_view
        
        self.stack_widget.addWidget(self.file_view)
        self.stack_widget.addWidget(self.date_view)
        self.stack_widget.addWidget(self.duplicates_view)
        
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.content_layout.addWidget(self.progress_bar)
        
        # Navigation bar
        self.navigation_bar = NavigationBar(self)
        self.navigation_controller = NavigationController(self.navigation_bar, self)
        self.content_layout.addWidget(self.navigation_bar)

        # Añado el stack de widgets por debajo de la barra de navegación
        self.content_layout.addWidget(self.stack_widget)


        self.main_layout.addLayout(self.content_layout)

    def setup_connections(self):
        # Navigation connections
        self.navigation_bar.to_original_button.clicked.connect(self.reorganize_to_original)
        self.navigation_bar.order_by_date_button.clicked.connect(self.reorganize_files)
        
        # Sidebar connections

        # self.theme_manager = ThemeManager()
        # self.sidebar.theme_change_button.clicked.connect(self.theme_manager.toggle_theme)
        

    def change_view(self, view_widget):
        """Método público para cambiar la vista actual"""
        self.stack_widget.setCurrentWidget(view_widget)
        self.actual_view = view_widget
        self.view_changed.emit(view_widget)


    def reorganize_files(self):
        
        if self.stack_widget.currentWidget() == self.file_view:
            self.navigation_controller.toggle_date_view()
 

        if FileOrganizer.contains_date(self.navigation_controller.current_path):
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
        msg_box.setText(f"Se modificarán los archivos del sistema en la carpeta {self.navigation_controller.current_path}. ¿Está seguro de continuar?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.button(QMessageBox.Yes).setText("Sí")

            
        if msg_box.exec() == QMessageBox.Yes:
            # Limpiar thread anterior si existe
            if hasattr(self, 'scan_thread') and self.scan_thread is not None:
                if self.scan_thread.isRunning():
                    self.scan_thread.quit()  # Esperar a que termine
            FileOrganizer.reorganize_by_date(
                self.date_view.get_files_by_date(),
                self.navigation_controller.current_path
            )
            self.navigation_controller.show_date_view()  # Actualizar la vista

    def reorganize_to_original(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar deshacer reorganización")
        msg_box.setText("Se reorganizarán los archivos al directorio original. ¿Está seguro de continuar?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.button(QMessageBox.Yes).setText("Sí")
        
        if msg_box.exec() == QMessageBox.Yes:
            FileOrganizer.restore_original_structure(self.navigation_controller.current_path)
            QMessageBox.information(self, "Proceso Completo", 
                                  "Los archivos han sido reorganizados a sus carpetas originales.")
            self.stack_widget.setCurrentWidget(self.file_view)  # Actualizar la vista
