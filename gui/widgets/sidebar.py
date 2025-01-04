from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QAction
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from core.theme_manager import ThemeManager

class Sidebar(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = ThemeManager()
        self.setup_ui()
        
    def setup_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        
        # Layout superior para los botones principales
        upper_layout = QVBoxLayout()
        upper_layout.setAlignment(Qt.AlignTop)
        
        # Crear botones principales
        self.reorganize_button = QPushButton("Reorganizar Archivos")
        self.duplicates_button = QPushButton("Eliminar Duplicados")
        
        upper_layout.addWidget(self.reorganize_button)
        upper_layout.addWidget(self.duplicates_button)
        
        # Widget contenedor para el layout superior
        upper_container = QWidget()
        upper_container.setLayout(upper_layout)

        # Botón de tema con tamaño fijo
        self.theme_change_button = QPushButton("Modo Claro")
        self.theme_change_button.setFixedHeight(30)
        self.theme_change_button.setIcon(QIcon("Assets/sol.svg"))
        
        
        # Agregar widgets al layout principal
        main_layout.addWidget(upper_container, stretch=1)  # stretch=1 hace que tome el espacio disponible
        main_layout.addWidget(self.theme_change_button)



        # layout = QVBoxLayout(self)
        
        # layout.setAlignment(Qt.AlignTop)
        
        # self.theme_change_button = QPushButton("Toggle Theme")
        #  # self.theme_action.setIcon(QIcon("path/to/theme_icon.png"))
        
        # layout.addWidget(self.theme_change_button)
