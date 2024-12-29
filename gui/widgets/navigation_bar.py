from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QDir
from enum import Enum

class ViewMode(Enum):
    NORMAL = "normal"
    DATE = "date"
    DUPLICATES = "duplicates"

class NavigationBar(QWidget):
    # Señales para comunicar eventos a la lógica
    path_changed = pyqtSignal(str)
    directory_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setUpdatesEnabled(False)  # Deshabilitar actualizaciones durante la inicialización
        self.current_view = ViewMode.NORMAL
        self.setup_ui()

        
    def setup_ui(self):

        # Layout principal vertical
        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.setSpacing(5)
        self.vertical_layout.setContentsMargins(5, 5, 5, 5)

        # Layout superior para la barra de dirección
        self.path_layout = QHBoxLayout()

        # Widget de entrada de dirección
        self.path_entry = QLineEdit()
        self.path_entry.setPlaceholderText(QDir.homePath())
        self.path_entry.returnPressed.connect(self._on_path_entered)

        # Botón de browse
        self.browse_button = QPushButton("...")
        self.browse_button.setFixedWidth(30)
        self.browse_button.clicked.connect(self._on_browse_clicked)
        
        # Agregar widgets al layout de dirección
        self.path_layout.addWidget(self.path_entry)
        self.path_layout.addWidget(self.browse_button)

        # Layout inferior para los botones
        self.buttons_layout = QHBoxLayout()
        self.create_buttons()
        
        # Agregar los layouts al layout principal
        self.vertical_layout.addLayout(self.path_layout)
        self.vertical_layout.addLayout(self.buttons_layout)

        self.main_layout = QHBoxLayout(self)
        self.create_buttons()
        
        # Actualizar a la vista inicial
        self.update_view(self.current_view)

    def hide_all_buttons(self):
        """Hide all buttons without removing them from layout"""
        for button in self.common_buttons.values():
            button.hide()
        for mode_buttons in self.view_buttons.values():
            for button in mode_buttons.values():
                button.hide()

    def create_buttons(self):
        """Create all possible buttons"""
        # Common buttons (always visible)
        self.common_buttons = {
            'home_button': QPushButton(QIcon("Assets/home.svg"), ""),
            'back_button': QPushButton(QIcon("Assets/flecha-pequena-izquierda.svg"), ""),
            'forward_button': QPushButton(QIcon("Assets/Adelante.svg"), ""),
            'up_button': QPushButton(QIcon("Assets/arriba.svg"), ""),
            # 'select_folder_button': QPushButton("Seleccionar Carpeta")
        }

        # Añadir botones comunes al layout inmediatamente
        for button in self.common_buttons.values():
            button.hide()  # Ocultar inicialmente
            self.buttons_layout.addWidget(button)

        # Create button attributes for direct access
        self.home_button = self.common_buttons['home_button']
        self.back_button = self.common_buttons['back_button']
        self.forward_button = self.common_buttons['forward_button']
        self.up_button = self.common_buttons['up_button']
        # self.select_folder_button = self.common_buttons['select_folder_button']
        
        # View-specific buttons
        self.view_buttons = {
            ViewMode.NORMAL: {
                'to_original_button': QPushButton("Ordenar por nombre de carpetas"),
                'date_view_button': QPushButton("Ver por Fechas")
            },
            ViewMode.DATE: {
                'order_by_date_button': QPushButton("Ordenar por fecha"),
                'file_view_button': QPushButton("Vista de carpetas")
            },
            ViewMode.DUPLICATES: {
                'duplicates_button': QPushButton("Buscar Duplicados")
            }
        }
        # Añadir todos los botones específicos al layout inmediatamente
        for mode_buttons in self.view_buttons.values():
            for button in mode_buttons.values():
                button.hide()  # Ocultar inicialmente
                self.buttons_layout.addWidget(button)

        # Create view-specific button attributes
        self.date_view_button = self.view_buttons[ViewMode.NORMAL]['date_view_button']
        self.to_original_button = self.view_buttons[ViewMode.NORMAL]['to_original_button']
        self.file_view_button = self.view_buttons[ViewMode.DATE]['file_view_button']
        self.order_by_date_button = self.view_buttons[ViewMode.DATE]['order_by_date_button']
        self.duplicates_button = self.view_buttons[ViewMode.DUPLICATES]['duplicates_button']

    def _on_path_entered(self):
        """Slot interno para manejar cuando se presiona Enter en el path_entry"""
        self.path_changed.emit(self.path_entry.text())
        
    def _on_browse_clicked(self):
        """Slot interno para manejar el click en el botón browse"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Directorio",
            self.path_entry.text(),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if directory:
            self.directory_selected.emit(directory)

    def update_path_display(self, path: str):
        """Actualizar el texto mostrado en el path_entry"""
        self.path_entry.setText(path)

        

    def update_view(self, view_mode: ViewMode):
        
        """Update the navigation bar for the specified view mode"""
        self.setUpdatesEnabled(False)  # Deshabilitar actualizaciones durante el cambio de pantalla
        self.current_view = view_mode
        

        # Ocultar todos los botones primero
        self.hide_all_buttons()

        # Mostrar botones comunes
        for button in self.common_buttons.values():
            button.show()

        # Mostrar botones específicos de la vista
        if view_mode in self.view_buttons:
            for button in self.view_buttons[view_mode].values():
                button.show()
        
        # Add stretch at the end
        self.buttons_layout.addStretch()

        self.setUpdatesEnabled(True) # Vuelve a activar las actualizaciones