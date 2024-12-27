from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer
from enum import Enum

class ViewMode(Enum):
    NORMAL = "normal"
    DATE = "date"
    DUPLICATES = "duplicates"


class NavigationBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
         # Evitar parpadeos durante la inicialización
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setUpdatesEnabled(False)  # Deshabilitar actualizaciones durante la inicialización
        
        self.current_view = ViewMode.NORMAL
        self.setup_ui()

        # Habilitar actualizaciones después de la inicialización
        # QTimer.singleShot(0, lambda: self.setUpdatesEnabled(True))
        
    def setup_ui(self):
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
            'select_folder_button': QPushButton("Seleccionar Carpeta")
        }

        # Añadir botones comunes al layout inmediatamente
        for button in self.common_buttons.values():
            button.hide()  # Ocultar inicialmente
            self.main_layout.addWidget(button)

        # Create button attributes for direct access
        self.home_button = self.common_buttons['home_button']
        self.back_button = self.common_buttons['back_button']
        self.forward_button = self.common_buttons['forward_button']
        self.up_button = self.common_buttons['up_button']
        self.select_folder_button = self.common_buttons['select_folder_button']
        
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
                self.main_layout.addWidget(button)

        # Create view-specific button attributes
        self.date_view_button = self.view_buttons[ViewMode.NORMAL]['date_view_button']
        self.to_original_button = self.view_buttons[ViewMode.NORMAL]['to_original_button']
        self.file_view_button = self.view_buttons[ViewMode.DATE]['file_view_button']
        self.order_by_date_button = self.view_buttons[ViewMode.DATE]['order_by_date_button']
        self.duplicates_button = self.view_buttons[ViewMode.DUPLICATES]['duplicates_button']

    def clear_layout(self):
        """Remove all widgets from layout"""
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().hide()

        

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
        self.main_layout.addStretch()

        self.setUpdatesEnabled(True) # Vuelve a activar las actualizaciones


    def get_button(self, button_name: str):
        """Get a button by its name"""
        if button_name in self.common_buttons:
            return self.common_buttons[button_name]
            
        for view_buttons in self.view_buttons.values():
            if button_name in view_buttons:
                return view_buttons[button_name]
        return None
        
    def connect_button(self, button_name: str, slot):
        """Connect a button's clicked signal to a slot"""
        button = self.get_button(button_name)
        if button:
            button.clicked.connect(slot)